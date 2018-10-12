# Copyright (c) 2016 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from cassandra import query
from cassandra.query import dict_factory
from oslo_log import log
from six.moves import filterfalse

from poppy.model import ssl_certificate
from poppy.storage import base


LOG = log.getLogger(__name__)

CQL_CREATE_CERT = '''
    INSERT INTO certificate_info (project_id,
        flavor_id,
        cert_type,
        domain_name,
        cert_details
        )
    VALUES (%(project_id)s,
        %(flavor_id)s,
        %(cert_type)s,
        %(domain_name)s,
        %(cert_details)s)
'''

CQL_SEARCH_CERT_BY_DOMAIN = '''
    SELECT project_id,
        flavor_id,
        cert_type,
        domain_name,
        cert_details
    FROM certificate_info
    WHERE domain_name = %(domain_name)s
'''

CQL_GET_CERTS_BY_STATUS = '''
    SELECT domain_name
    FROM cert_status WHERE status = %(status)s
'''

CQL_DELETE_CERT = '''
    DELETE FROM certificate_info
    WHERE domain_name = %(domain_name)s
'''

CQL_DELETE_CERT_STATUS = '''
    DELETE FROM cert_status
    WHERE domain_name = %(domain_name)s
'''


CQL_INSERT_CERT_STATUS = '''
    INSERT INTO cert_status (domain_name,
        status
        )
    VALUES (%(domain_name)s,
        %(status)s)
'''

CQL_UPDATE_CERT_DETAILS = '''
    UPDATE certificate_info
    set cert_details = %(cert_details)s
    WHERE domain_name = %(domain_name)s
    IF cert_type = %(cert_type)s AND flavor_id = %(flavor_id)s
'''


class CertificatesController(base.CertificatesController):

    """Certificates Controller."""

    @property
    def session(self):
        """Get session.

        :returns session
        """
        return self._driver.database

    def create_certificate(self, project_id, cert_obj):
        if self.cert_already_exist(domain_name=cert_obj.domain_name,
                                   comparing_cert_type=cert_obj.cert_type,
                                   comparing_flavor_id=cert_obj.flavor_id,
                                   comparing_project_id=project_id):
            raise ValueError('Certificate already exists '
                             'for {0} '.format(cert_obj.domain_name))

        args = {
            'project_id': project_id,
            'flavor_id': cert_obj.flavor_id,
            'cert_type': cert_obj.cert_type,
            'domain_name': cert_obj.domain_name,
            # when create the cert, cert domain has not been assigned yet
            # In future we can tweak the logic to assign cert_domain
            # 'cert_domain': '',
            'cert_details': cert_obj.cert_details
        }
        stmt = query.SimpleStatement(
            CQL_CREATE_CERT,
            consistency_level=self._driver.consistency_level)
        self.session.execute(stmt, args)

        cert_status = None
        try:
            provider_status = json.loads(
                list(cert_obj.cert_details.values())[0]
            )
            cert_status = provider_status['extra_info']['status']
        except (IndexError, KeyError, ValueError) as e:
            LOG.warning(
                "Create certificate missing extra info "
                "status {0}: Error {1}. "
                "Using 'create_in_progress' instead. ".format(
                    cert_obj.cert_details, e))
            cert_status = 'create_in_progress'
        finally:
            # insert/update for cassandra
            self.insert_cert_status(cert_obj.domain_name, cert_status)

    def delete_certificate(self, project_id, domain_name, cert_type):
        args = {
            'domain_name': domain_name.lower()
        }

        stmt = query.SimpleStatement(
            CQL_SEARCH_CERT_BY_DOMAIN,
            consistency_level=self._driver.consistency_level)
        result_set = self.session.execute(stmt, args)
        complete_results = list(result_set)
        if complete_results:
            for r in complete_results:
                r_project_id = str(r.get('project_id'))
                r_cert_type = str(r.get('cert_type'))
                if r_project_id == str(project_id) and \
                        r_cert_type == str(cert_type):
                    args = {
                        'domain_name': str(r.get('domain_name'))
                    }
                    stmt = query.SimpleStatement(
                        CQL_DELETE_CERT,
                        consistency_level=self._driver.consistency_level)
                    self.session.execute(stmt, args)
                    stmt = query.SimpleStatement(
                        CQL_DELETE_CERT_STATUS,
                        consistency_level=self._driver.consistency_level)
                    self.session.execute(stmt, args)
        else:
            raise ValueError(
                "No certificate found for: {0},"
                "type: {1}".format(domain_name, cert_type))

    def update_certificate(self, domain_name, cert_type, flavor_id,
                           cert_details):

        args = {
            'domain_name': domain_name,
            'cert_type': cert_type,
            'flavor_id': flavor_id,
            'cert_details': cert_details
        }
        stmt = query.SimpleStatement(
            CQL_UPDATE_CERT_DETAILS,
            consistency_level=self._driver.consistency_level)
        self.session.execute(stmt, args)

        try:
            provider_status = json.loads(list(cert_details.values())[0])
            cert_status = provider_status['extra_info']['status']
            self.insert_cert_status(domain_name, cert_status)
        except (IndexError, KeyError, ValueError) as e:
            # certs already existing in DB should have all
            # the necessary fields
            LOG.error(
                "Unable to update cert_status because certificate "
                "details are in  an inconsistent "
                "state: {0}: {1}".format(cert_details, e))

    def insert_cert_status(self, domain_name, cert_status):
            cert_args = {
                'domain_name': domain_name,
                'status': cert_status
            }
            stmt = query.SimpleStatement(
                CQL_INSERT_CERT_STATUS,
                consistency_level=self._driver.consistency_level)
            self.session.execute(stmt, cert_args)

    def get_certs_by_status(self, status):

        LOG.info("Getting domains which have "
                 "certificate in status : {0}".format(status))
        args = {
            'status': status
        }
        stmt = query.SimpleStatement(
            CQL_GET_CERTS_BY_STATUS,
            consistency_level=self._driver.consistency_level)
        resultset = self.session.execute(stmt, args)
        complete_results = list(resultset)

        return complete_results

    def get_certs_by_domain(self, domain_name, project_id=None,
                            flavor_id=None,
                            cert_type=None):
        """Get certificate details associated with the given domain name.

        The cassandra table ``certificate_info`` stores the certificates
        details for domain names. The field ``domain_name`` is a unique
        key in that table hence it is always guaranteed that for any
        given domain name there is one and only one matching certificate.

        List of valid ``cert_type``:
            - san
            - sni
            - custom
            - dedicated

        :param unicode domain_name: The name of the domain
        :param unicode project_id: The project id
        :param unicode flavor_id: The flavor id
        :param unicode cert_type: Type of the certificate

        :return: Matching SSLCertificate object for the domain
        :rtype: poppy.model.ssl_certificate.SSLCertificate

        :raises ValueError: If no matching certificate found
        """
        LOG.info("Check if cert on '{0}' exists".format(domain_name))
        args = {
            'domain_name': domain_name.lower(),
        }

        stmt = query.SimpleStatement(CQL_SEARCH_CERT_BY_DOMAIN,
            consistency_level=self._driver.consistency_level)
        self.session.row_factory = dict_factory
        result = self.session.execute(stmt, args)

        try:
            cert_obj = result[0]
            for k, v in cert_obj.items():
                if k == "cert_details":
                    # Cassandra returns OrderedMapSerializedKey for
                    # cert_details. Converting it to python dict.
                    cert_details  = {}
                    for x,y in cert_obj[k].items():
                        cert_details[x] = json.loads(y)
                    cert_obj[k] = cert_details
                else:
                    cert_obj[k] = str(v)

            ssl_cert = ssl_certificate.SSLCertificate.init_from_dict(cert_obj)

            # Check that all supplied optional parameters
            # (project_id, flavor_id and cert_type ) with non-none values
            # are matching with the values returned from database.
            params = {
                'project_id': project_id,
                'flavor_id': flavor_id,
                'cert_type': cert_type
            }
            non_none_args = [(k, v) for k, v in params.items() if v is not None]
            for name, value in non_none_args:
                if getattr(ssl_cert, name) != value:
                    raise ValueError("No matching certificates found for "
                                     "the domain {}".format(domain_name))

            return ssl_cert
        except:
            raise ValueError("No matching certificates found for "
                             "the domain {}".format(domain_name))

    def cert_already_exist(self, domain_name, comparing_cert_type,
                           comparing_flavor_id, comparing_project_id):
        """Check if a certificate exists for the given domain name.

        Check if a cert with this domain name and type has already been
        created, or if the domain has been taken by other customers.

        List of valid ``cert_type``:
            - san
            - sni
            - custom
            - dedicated

        :param unicode domain_name: The name of the domain
        :param unicode comparing_cert_type: Type of the certificate
        :param unicode comparing_flavor_id: Flavor id
        :param unicode comparing_project_id: Project id

        :returns: ``True`` if there is already a certificate exists
            for the given domain name. Else ``False``.
        :rtype: bool
        """
        try:
            self.get_certs_by_domain(
            domain_name=domain_name,
            cert_type=comparing_cert_type,
            flavor_id=comparing_flavor_id
        )
            return True
        except ValueError:
            return False
