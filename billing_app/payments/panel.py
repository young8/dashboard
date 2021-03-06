from django.utils.translation import ugettext_lazy as _

import horizon

from billing_app import dashboard


class Payments(horizon.Panel):
    name = _("Manage Payments")
    slug = "payments"


dashboard.Billing_App.register(Payments)
