import billing
from django.core.exceptions import ObjectDoesNotExist  # noqa
from django.db import (models, IntegrityError)  # noqa
from django.utils.translation import ugettext_lazy as _


class StripeCustomerManager(models.Manager):

    def create_stripe_customer(self, name, is_default,
                               tenant_id, stripe_customer_id):
        card = self.model(name=name,
                          is_default=is_default,
                          tenant_id=tenant_id,
                          stripe_customer_id=stripe_customer_id)

        # make the card default there's no other
        if not self.filter(tenant_id__exact=tenant_id):
            card.is_default = True
        try:
            card.save()
        except IntegrityError:
            return (False, _("You already have a card"
                             " by the number :- %s") % card.name)
        except Exception:
            return (False, _("Could not add card. Try again later."))

        if card.is_default:
            return self.ensure_default(card.id, tenant_id)

        return (True,)

    def ensure_default(self, id, tenant_id):
        try:
            old_defaults = self.filter(tenant_id__exact=tenant_id,
                                       is_default=True).exclude(id__exact=id)
            for card in old_defaults:
                card.is_default = False
                card.save()

            new_default = self.get(id__exact=id,
                                   tenant_id__exact=tenant_id)

            new_default.is_default = True
            new_default.save()
            return (True,)
        except Exception:
            return (False, _("Card added but not as default."))

    def delete_card(self, id, tenant_id):
        stripe = billing.get_gateway("stripe").stripe
        try:
            card = self.get(
                id__exact=id,
                tenant_id__exact=tenant_id
            )
            stripe_cust = stripe.Customer.retrieve(card.stripe_customer_id)
            stripe_cust.delete()
            card.delete()
            return (True,)
        except stripe.error.StripeError as e:
            # Display a very generic error to the user
            if e.http_status == 404:
                card.delete()
                return (True,)
            return (False, e.message)
        except ObjectDoesNotExist as e:
            return (False, u'Card does not exist')
        except Exception:
            return (False, _("Could not delete card. "
                             "Please try again later"))


class MobileMoneyNumberManager(models.Manager):

    def add_number(self, number, tenant_id):
        mobilenumber = self.model(number=number, tenant_id=tenant_id)

        try:
            mobilenumber.save()
        except IntegrityError:
            return (False, _("That number %s isn't available"
                             "for use") % mobilenumber.number)
        except Exception:
            return (False, _("Could not add number. Try again later."))

        return (True,)

    def delete_number(self, id, tenant_id):
        try:
            mobilenumber = self.get(
                id__exact=id,
                tenant_id__exact=tenant_id
            )
            mobilenumber.delete()
            return (True,)
        except IntegrityError:
            return (False, _("That number %s isn't available"
                             "for use") % mobilenumber.number)
        except Exception:
            return (False, _("Could not delete Number. "
                             "Please try again later"))
        return (True,)


class K2RawDataManager(models.Manager):

    def create(self, k2data):
        k2_entry = self.model(
            service_name=k2data['service_name'],
            business_number=k2data['business_number'],
            transaction_reference=k2data['transaction_reference'],
            internal_transaction_id=k2data['internal_transaction_id'],
            transaction_timestamp=k2data['transaction_timestamp'],
            transaction_type=k2data['transaction_type'],
            account_number=k2data['account_number'],
            sender_phone=k2data['sender_phone'],
            first_name=k2data['first_name'],
            middle_name=k2data['middle_name'],
            last_name=k2data['last_name'],
            amount=k2data['amount'],
            currency=k2data['currency'],
            signature=k2data['signature'])
        k2_entry.save()
