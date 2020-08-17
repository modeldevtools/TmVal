from collections import namedtuple
import decimal
import numpy as np
from typing import Callable, Union

from tmval.value import Payments, Rate
from tmval.growth import Accumulation
from math import ceil


class Annuity(Payments):

    def __init__(
        self,
        gr: Union[float, Rate, Accumulation, Callable],
        period: float = None,
        term: float = None,
        amount: Union[float, list] = 1.0,
        times: list = None,
        imd: str = 'immediate'
    ):
        self.term = term
        self.amount = amount
        self.period = period
        self.imd = imd
        imd_ind = 1 if imd == 'immediate' else 0
        self.is_level_pmt = None

        if term == np.inf:

            amounts = [np.inf]
            times = [np.inf]
            self._ann_perp = 'perpetuity'
        else:

            if isinstance(amount, float) or isinstance(amount, list) and len(amount) == 1:
                n_payments = term / period
                n_payments = int(ceil(n_payments))
                amounts = [amount] * n_payments
                times = [period * (x + imd_ind) for x in range(n_payments)]
                self.is_level_pmt = True
            else:
                amounts = amount
                times = times
                times.sort()
                intervals = list(np.diff(times))
                intervals = [round(x, 7) for x in intervals]
                if intervals[1:] != intervals[:-1]:
                    raise Exception("Non-level intervals detected, use Payments class instead.")
                else:
                    self.period = intervals[0]

                if amounts[1:] == amounts[:-1]:
                    self.is_level_pmt = False

                if min(times) == 0:
                    self.imd = 'due'
                    self.term = max(times) + self.period
                else:
                    self.imd = 'immediate'
                    self.term = max(times)

            self._ann_perp = 'annuity'

        Payments.__init__(
            self,
            amounts=amounts,
            times=times,
            gr=gr
        )

        self.pattern = self._ann_perp + '-' + imd

        if imd not in ['immediate', 'due']:
            raise ValueError('imd can either be immediate or due.')

    def pv(self):

        # if interest rate is level, can use formulas to save time
        if isinstance(self.gr, Accumulation) and self.gr.is_level and self.is_level_pmt:

            if self._ann_perp == 'perpetuity':

                pv = self.amount / (self.gr.val(self.period) - 1)

            else:

                pv = self.amount * \
                     (1 - self.gr.discount_func(self.term)) /\
                     (self.gr.val(self.period) - 1)

                if self.imd == 'due':
                    pv = pv * self.gr.val(self.period)

        # otherwise, use npv function
        else:
            pv = self.npv()

        return pv

    def sv(self):

        if isinstance(self.gr, Accumulation) and self.gr.is_level and self.is_level_pmt:
            sv = self.amount * \
                 ((1 + self.gr.interest_rate) ** self.term - 1) / \
                 (self.gr.val(self.period) - 1)

            if self.imd == 'due':
                sv = sv * self.gr.val(self.period)

        else:

            sv = self.eq_val(t=self.term)

        return sv


def get_loan_amt(
        down_pmt: float,
        loan_pmt: float,
        period: float,
        term: float,
        gr: Rate
) -> float:

    ann = Annuity(
        period=period,
        term=term,
        amount=loan_pmt,
        gr=gr
    )

    loan_amt = ann.pv() + down_pmt

    return loan_amt


def get_loan_pmt(
        loan_amt: float,
        period: float,
        term: float,
        gr: Rate,
        imd: str = 'immediate',
        cents=False
):

    ann = Annuity(
        period=period,
        term=term,
        gr=gr,
        imd=imd
    )

    pmt = loan_amt / ann.pv()

    if cents:

        acc = Accumulation(gr=gr)

        pmt_round = round(pmt, 2)

        pv = Annuity(
            amount=pmt_round,
            period=period,
            term=term,
            gr=gr,
            imd=imd
        ).pv()

        if loan_amt == round(pv, 2):

            return pmt

        else:

            cent = decimal.Decimal('0.01')

            pmt_round2 = float(
                decimal.Decimal(pmt).quantize(
                    cent,
                    rounding=decimal.ROUND_UP
                )
            )

            diff = Annuity(
                amount=pmt_round2,
                period=period,
                term=term,
                gr=gr,
                imd=imd
            ).pv() - loan_amt

            last_pmt = pmt_round2 - round(diff * acc.val(t=term), 2)

            Installments = namedtuple(
                'installments',
                'amount last'
            )

            return Installments(pmt_round2, last_pmt)
    else:
        return pmt


def get_savings_pmt(
        fv: float,
        period: float,
        term: float,
        gr: Rate,
        cents=False
):

    ann = Annuity(
        period=period,
        term=term,
        gr=gr
    )

    pmt = fv / ann.sv()

    if cents:
        pmt_round = round(pmt, 2)

        fv2 = Annuity(
            amount=pmt_round,
            period=period,
            term=term,
            gr=gr
        ).sv()

        if fv == round(fv2, 2):

            return pmt

        else:
            cent = decimal.Decimal('0.01')

            pmt_round2 = float(
                decimal.Decimal(pmt).quantize(
                    cent,
                    rounding=decimal.ROUND_UP
                )
            )

            diff = Annuity(
                amount=pmt_round2,
                period=period,
                term=term,
                gr=gr
            ).sv() - fv

            last_pmt = round(pmt_round2 - round(diff, 2), 2)

            Installments = namedtuple('installments', 'amount last')

            return Installments(pmt_round2, last_pmt)
    else:
        return pmt


def get_number_of_pmts(
        pmt: float,
        fv: float,
        period: float,
        gr: Rate
):
    i = gr.convert_rate(
        'Effective Interest',
        interval=period
    )

    n = np.log(fv / pmt * i + 1) / np.log(1 + i)

    n = ceil(n)

    return n


def olb_r(
        loan: float,
        q: float,
        period: float,
        gr: Union[Accumulation, float, Rate],
        t
) -> float:

    ann = Annuity(
        period=period,
        term=t,
        gr=gr,
        amount=q
    )

    acc = Accumulation(gr=gr)
    olb = loan * acc.val(t) - ann.sv()

    return max(olb, 0)


def olb_p(
    q: float,
    period: float,
    term: float,
    gr: Union[float, Rate, Accumulation],
    t: float,
    r: float = None,
    missed: list = None
) -> float:
    """
    Outstanding loan balance - prospective method.

    :param q:
    :type q:
    :param period:
    :type period:
    :param term:
    :type term:
    :param gr:
    :type gr:
    :param t:
    :type t:
    :param r:
    :type r:
    :param missed:
    :type missed:
    :return:
    :rtype:
    """
    acc = Accumulation(gr=gr)

    if r is not None:
        ann = Annuity(
            period=period,
            term=term - t - period,
            gr=gr,
            amount=q
        )

        r_pv = r * acc.discount_func(term - t)

        olb = ann.pv() + r_pv

    else:
        ann = Annuity(
            period=period,
            term=term - t,
            gr=gr,
            amount=q
        )

        olb = ann.pv()

    if missed:

        for p in missed:
            olb += q * acc.val(t - p)

    return olb
