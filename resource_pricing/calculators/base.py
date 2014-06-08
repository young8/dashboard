from django.conf import settings
from django.core import exceptions
from resource_pricing import models
from resource_pricing import types


class CalculatorBase(object):
    types = types.ResourceTypes()
    type_name = None
    required_params = []
    optional_params = []

    def __init__(self):
        if not self._type_is_configured():
            raise Exception("the type {0} is not configured".format(
                self.type_name))

    def _type_is_configured(self):
        if self.type_name in settings.BILLABLE_RESOURCE_TYPES.keys():
            return True
        return False

    def _validate_params(self, params):
        for x in self.required_params:
            if x not in params:
                raise Exception("the required parameter {0} is missing".
                                format(x))
        for x in params.keys():
            if (x not in self.optional_params and
                    x not in self.required_params):
                raise Exception("the given parameter {0} is unknown".
                                format(x))
        self._specific_param_checks(params)

    def _get_resource_price(self, resource_id, currency="USD"):
        try:
            price = models.Price.objects.get(currency__iso=currency,
                                             resource=resource_id)
        except exceptions.ObjectDoesNotExist:
            raise Exception("Could not find price for resource {0} with"
                            " currency {1}".format(resource_id, currency))
        return price.price

    def _specific_param_checks(self, params):
        pass


class VolumeAndInstancePriceCalculatorBase(CalculatorBase):

    def __init__(self):
        super(VolumeAndInstancePriceCalculatorBase, self).__init__()

    def _get_unit_price(self, type_id, currency="USD"):
        try:
            price = models.Price.objects.get(
                **{"currency__iso": currency,
                   self.resource_type_relation: type_id})
        except exceptions.ObjectDoesNotExist:
            raise Exception("Could not get price of type {0} in currency "
                            "{1}".format(type_id, currency))
        return price.price

    def _specific_param_checks(self, params):
        if params['hours'] < 0:
            raise Exception('the consumed hours cannot be less than 0')

    def get_price(self, params=None):
        self._validate_params(params)
        return self._final_calculation(params, self._get_unit_price(
            params[self.type_key]))
