# Copyright (c) 2013 Mirantis Inc.
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

from sqlalchemy.ext import declarative

from savanna.openstack.common.db.sqlalchemy import models as oslo_models


class _SavannaBase(oslo_models.ModelBase, oslo_models.TimestampMixin):
    """Base class for all Savanna SQLAlchemy DB Models."""

    def to_dict(self):
        """sqlalchemy based automatic to_dict method."""
        d = {}
        for col in self.__table__.columns:
            d[col.name] = getattr(self, col.name)

        self._datetime_to_str(d, 'created_at')
        self._datetime_to_str(d, 'updated_at')

        return d

    def _datetime_to_str(self, dct, attr_name):
        if dct.get(attr_name) is not None:
            dct[attr_name] = dct[attr_name].isoformat(' ')

SavannaBase = declarative.declarative_base(cls=_SavannaBase)
