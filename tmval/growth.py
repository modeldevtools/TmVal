"""
Contains general amount functions implemented as Amount and Accumulation classes.
The simple and compound interest cases are represented as subclasses SimpleAmt and CompoundAmt, respectively.
"""
from __future__ import annotations

import datetime as dt
import numpy as np

from inspect import signature
from typing import Callable, Union

from tmval.rates import Rate, standardize_rate


class Amount:
    """
    The Amount class is an implementation of the amount function, which describes how much an invested
    amount of money grows over time.

    The amount function's methods can return things like the valuation of an investment after a
    specified time, and effective interest and discount rates over an interval.

    The accumulation function, which is a special case of the amount function where k=1, can be extracted
    from the amount function using the get_accumulation() method.


    :param gr: a growth object, which can either be a function that must take the parameters t \
    for time and k for principal, or a Rate object representing an interest rate.
    :type gr: Callable, Rate
    :param k: the principal, or initial investment.
    :type k: float

    :return: An amount object, which can be used like an amount function in interest theory.
    :rtype: Amount

    """
    def __init__(
            self,
            gr: Union[Callable, Rate, float],
            k: float
    ):
        self.__gr = gr
        self.func = self.__extract_func()
        self.k = k

        self._validate_func()

    def __extract_func(self):

        if isinstance(self.__gr, Callable):
            return self.__gr
        elif isinstance(self.__gr, Rate):
            return self.__gr.amt_func
        else:
            raise Exception("Growth object must be a callable or Rate object.")

    def _validate_func(self):
        """
        Check if func object is properly formed.
        """
        sig = signature(self.func)

        # check return type
        # if not isinstance(sig.return_annotation, float):
        #     raise TypeError("Growth function must return a float, got type " + str(sig.return_annotation))

        # check arguments
        if 'k' not in sig.parameters:
            raise Exception("Growth function must take a parameter k for the principal.")

        if 't' not in sig.parameters:
            raise Exception("Growth function must take a parameter t for time.")

    def val(self, t: float) -> float:
        """
        Calculates the value of the investment at a point in time.

        :param t:evaluation date. The date at which you would like to know the value of the investment.
        :type t: float
        :return: the value of the investment at time t.
        :rtype: float
        """
        k = self.k
        return self.func(t=t, k=k)

    def interest_earned(
        self,
        t1: float,
        t2: float
    ) -> float:
        """
        Calculates the amount of interest earned over a time period.

        :param t1: beginning of the period.
        :type t1: float
        :param t2: end of the period.
        :type t2: float
        :return: The amount of interest earned over the time period.
        :rtype: float
        """
        if t2 < t1:
            raise Exception("t2 must be greater than t1")
        if t1 < 0 or t2 < 0:
            raise Exception("each time period must be greater than 0")

        interest_earned = self.val(t=t2) - self.val(t=t1)
        return interest_earned

    def effective_interval(
            self,
            t2: float,
            t1: float = 0,
            annualized: bool = False
    ) -> Rate:
        """
        Calculates the effective interest rate over a time period.

        :param t1: the beginning of the period.
        :type t1: float
        :param t2: the end of the period.
        :type t2: float
        :return: the effective interest rate over the time period.
        :rtype: float
        :param annualized: whether you want the results to be annualized.
        :rtype annualized: bool
        """

        interval = t2 - t1
        effective_rate = (self.val(t=t2) - self.val(t=t1)) / self.val(t=t1)

        effective_rate = Rate(
            rate=effective_rate,
            pattern="Effective Interest",
            interval=interval
        )

        if annualized:
            effective_rate = effective_rate.standardize()

        return effective_rate

    def effective_rate(
            self,
            n: int
    ) -> Rate:
        """
        Calculates the effective interest rate for the n-th time period.

        :param n: the n-th time period.
        :type n: int
        :return: the effective interest rate for the n-th timer period.
        :rtype: float
        """
        t1 = n - 1
        t2 = n
        effective_rate = self.effective_interval(
            t1=t1,
            t2=t2
        )

        return effective_rate

    def discount_interval(
        self,
        t1: float,
        t2: float
    ) -> float:
        """
        Calculates the effective discount rate over a time period.

        :param t1: the beginning of the time period.
        :type t1: float
        :param t2: the end of the time period.
        :type t2: float
        :return: the effective discount rate over the time period.
        :rtype: float
        """

        discount_rate = (self.val(t=t2) - self.val(t=t1)) / self.val(t=t2)
        return discount_rate

    def effective_discount(
        self,
        n: int
    ) -> float:
        """
        Calculates the effective discount rate for the n-th time period.

        :param n: the n-th time period.
        :type n: int
        :return: the effective discount rate for the n-th time period.
        :rtype: float
        """
        t1 = n - 1
        t2 = n
        effective_discount = self.discount_interval(
            t1=t1,
            t2=t2
        )
        return effective_discount

    def get_accumulation(self) -> Accumulation:
        """
        Extracts the :term:`accumulation function`, a special case of the amount function where k=1.

        :return: the accumulation function.
        :rtype: Accumulation
        """
        amt_func = self.func

        def acc_func(t):
            return amt_func(k=1, t=t)

        accumulation = Accumulation(gr=acc_func)
        return accumulation


class Accumulation(Amount):
    """
    Special case of Amount function where k=1,
    Accepts an accumulation amount function,
    can return valuation at time t and effective interest rate on an interval

    :param gr: a growth object, which can either be a function that must take the parameters t \
    for time and k for principal, or a Rate object representing an interest rate.
    :type gr: Callable, Rate
    :return: an accumulation object.
    :rtype: Accumulation
    """
    def __init__(
        self,
        gr: Union[Callable, Rate]
    ):
        super().__init__(
            gr=gr,
            k=1
        )

        self.__gr = gr
        self.func = self.__extract_func()

    def __extract_func(self):

        if isinstance(self.__gr, Callable):
            params = signature(self.__gr).parameters

            if 'k' in params:
                def f(t: float) -> float:
                    return self.__gr(t=t, k=1)
            else:
                f = self.__gr

            return f

        elif isinstance(self.__gr, Rate):
            return self.__gr.acc_func
        else:
            raise Exception("Growth object must be a callable or Rate object.")

    def _validate_func(self):
        """
        Check if func object is properly formed.
        """
        sig = signature(self.func)

        # check return type
        # if sig.return_annotation != 'float':
        #     raise TypeError("Growth function must return a float, got type " + str(sig.return_annotation))

        # check arguments

        if 't' not in sig.parameters:
            raise Exception("Growth function must take a parameter t for time.")

    def val(self, t: float) -> float:
        """
        Calculates the value of the investment at a point in time.

        :param t: evaluation date. The date at which you would like to know the value of the investment.
        :type t: float
        :return: the value of the investment at time t.
        :rtype: float
        """
        return self.func(t=t)

    def discount_func(self, t: float, fv: float = None) -> float:
        """
        The discount function is the reciprocal of the accumulation function. Returns the discount
        factor at time t, which can be used to get the present value of an investment.

        :param t: the time at which you would like to get the discount factor.
        :type t: float
        :param fv: float: the future value. Assumed to be 1 if not provided.
        :type fv: float, optional
        :return: the discount factor at time t
        :rtype: float
        """
        if fv is None:
            fv = 1

        return fv / self.val(t)

    def future_principal(
            self,
            fv: float,
            t1: float,
            t2: float
    ) -> float:
        """
        Finds the principal needed at t1 to get fv at t2.

        :param fv: future value.
        :type fv: float
        :param t1: time of investment.
        :type t1: float
        :param t2: time of goal.
        :type t2: float
        :return: amount of money needed at t1 to get fv at t2.
        :rtype: float
        """

        future_principal = fv * self.discount_func(t2) * self.val(t1)

        return future_principal


def simple_solver(
    pv: float = None,
    fv: float = None,
    s: Union[float, Rate] = None,
    t: float = None
):
    """
    Simple interest solver for when one variable is missing - returns missing value. You need to supply
    three out of the four arguments, and the function will solve for the missing one.

    :param pv: the present value
    :type pv: float
    :param fv: the future value
    :type fv: float
    :param s: the interest rate
    :type s: float
    :param t: the time
    :type t: float
    :return: the present value, future value, interest rate, or time - whichever is missing.
    :rtype: float
    """
    args = [pv, fv, s, t]
    if args.count(None) > 1:
        raise Exception("Only one argument can be missing.")

    if pv is None:
        res = fv / (1 + t * s)
    elif fv is None:
        res = pv * (1 + t * s)
    elif s is None:
        res = (fv / pv - 1) / t
        res = Rate(s=res)
    else:
        res = (fv / pv - 1) / s

    return res


def osi(
        beg_dt: dt.datetime,
        end_dt: dt.datetime,
        frac=True
) -> float:
    """
    Calculate the number of days using the ordinary simple interest or 30/360 rule.
    Set frac=True to return days as a percentage of year.

    :param beg_dt: beginning date
    :type beg_dt: datetime.datetime
    :param end_dt: ending date
    :type end_dt: datetime.datetime
    :param frac: whether you want the answer in number of days or fraction of a year, defaults to True
    :type frac: bool, optional
    :return: the number of days using the ordinary simple interest or 360 rule, or the percentage of year \
    if frac=True
    :rtype: float
    """
    y1 = beg_dt.year
    y2 = end_dt.year

    m1 = beg_dt.month
    m2 = end_dt.month

    d1 = beg_dt.day
    d2 = end_dt.day

    days = 360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)

    if frac:
        return days / 360
    else:
        return days


def bankers_rule(
        beg_dt: dt.datetime,
        end_dt: dt.datetime,
        frac=True
) -> float:
    """
    Calculate the number of days using the Banker's rule or actual/360 rule.
    Set frac=True to return days as a percentage of year.

    :param beg_dt: the beginning date
    :type beg_dt: datetime.datetime
    :param end_dt: the ending date
    :type end_dt: datetime.datetime
    :param frac: whether you want the answer in number of days or fraction of a year, defaults to True
    :type frac: bool, optional
    :return: the number of days or percent of a year between two dates using the Banker's rule or actual/360 rule, \
    depending on frac
    :rtype: float
    """

    delta = end_dt - beg_dt

    days = delta.days

    if frac:
        return days / 360
    else:
        return days


class CompoundAmt(Amount):
    """
    Compound interest scenario, special case of amount function where amount function is geometric. \
    :class:`CompoundAmt` is a subclass of the :class:`Amount` class in the case of compound interest. If \
    your problem involves compound interest, you should probably use this class or the :class:`CompoundAcc` class
    instead of the more general classes of :class:`Amount` and :class:`Accumulation`.

    With this class, you do not need to supply a growth function, just pass an interest rate and and the growth \
    function will be constructed automatically.

    :param k: principal, or the initial investment.
    :type k: float
    :param gr: the growth rate, can be a compound interest rate supplied as a float or a Rate object
    :type gr: float or Rate
    :return: a CompoundAmt object.
    :rtype: CompoundAmt
    """
    def __init__(
            self,
            k: float,
            gr: Union[float, Rate]
    ):

        # Convert to single-period compound interest first

        i = standardize_rate(gr)

        self.principal = k
        self.interest_rate = Rate(i)

        Amount.__init__(
            self,
            gr=self.amt_func,
            k=k
        )

    def amt_func(self, k, t):
        """
        The amount function of the :class:`CompoundAmt` class.
        Automatically applied to the :class:`Amount` class
        by providing a compound growth function, instead of a user-defined one.

        :param k: the principal, or initial investment.
        :type k: float
        :param t: the time as-of time for the valuation.
        :type t: float
        :return: the value of k at time t, invested at time 0.
        :rtype: float
        """
        return k * ((1 + self.interest_rate.rate) ** t)


class CompoundAcc(Accumulation):
    """
    Compound interest scenario, special case of accumulation function where amount function is geometric.  \
    :class:`CompoundAcc` is a subclass of the :class:`Accumulation` class in the case of compound interest. If \
    your problem involves compound interest, you should probably use this class or the :class:`CompoundAmt` class
    instead of the more general classes of :class:`Amount` and :class:`Accumulation`.

    :param gr: the growth rate, can be a compound interest rate supplied as a float or a Rate object
    :type gr: float or Rate
    :return: a CompoundAcc object.
    :rtype: CompoundAcc
    """

    def __init__(
            self,
            gr: Union[float, Rate]
    ):

        i = standardize_rate(gr)

        self.interest_rate = Rate(i)

        Accumulation.__init__(
            self,
            gr=self.acc_func
        )

    @property
    def discount_factor(self) -> float:
        discount_factor = 1 / (1 + self.interest_rate.rate)
        return discount_factor

    def acc_func(self, t) -> float:
        """
        The accumulation function of the :class:`CompoundAcc` class.
        Automatically applied to the :class:`Accumulation` class
        by providing a compound growth function, instead of a user-defined one.

        :param t: the time as-of time for the valuation.
        :type t: float
        :return: the value of 1 unit of currency at time t, invested at time 0.
        :rtype: float
        """
        return (1 + self.interest_rate.rate) ** t


def compound_solver(
    pv: float = None,
    fv: float = None,
    t: float = None,
    gr: Union[float, Rate] = None
):
    """
    Solves for a missing value in the case of compound interest supply 3/4 of: a present value, a future value \
    an interest rate (either APY or APR), and a time. If using an APR interest rate, you need to supply a compounding \
    frequency of m times per period, and you need to set the use_apr parameter to True.

    :param pv: the present value, defaults to None.
    :type pv: float
    :param fv: the future value, defaults to None.
    :type fv: float
    :param t: the time, defaults to None.
    :type t: float
    :type gr: a general growth rate.
    :type gr: Rate
    :return: either a present value, a future value, an interest rate, or a time, depending on which one is missing.
    :rtype: float
    """

    args = [pv, fv, gr, t]

    if args.count(None) > 1:
        raise Exception("You are missing either a present value (pv), future value(fv), "
                        "time (t), or growth rate.")

    if gr:
        i = standardize_rate(gr)

    else:
        i = None

    if pv is None:
        res = fv / ((1 + i) ** t)
    elif fv is None:
        res = pv * ((1 + i) ** t)
    elif gr is None:
        # get the effective rate first
        res = ((fv / pv) ** (1 / t)) - 1
        res = Rate(res)
    else:
        res = np.log(fv / pv) / np.log(1 + i)

    return res


class TieredBal:
    """
    :class:`TieredBal` is a callable growth pattern for tiered investment accounts. A tiered investment account is one \
    where the interest paid varies depending on the balance. For example, 1% for the first $1000, 2% for the next \
    $4000, and 3% afterward.

    To create a :class:`TieredBal`, supply a list of tiers and a corresponding list of interest rates for those tiers. \
    The tiers are the lower bounds for the intervals corresponding to the interest rate (the first value will \
    usually be 0).

    :param tiers: a list of tiers, for example [0, 1000, 5000].
    :type tiers: list
    :param rates: a list of interest rates, for example [.01, .02, .03].
    :type rates: list
    :return: a TieredBal object.
    :rtype: TieredBal
    """
    def __init__(
        self,
        tiers: list,
        rates: list
    ):
        self.tiers = tiers
        self.rates = rates

    def __call__(
        self,
        k: float,
        t: float
    ) -> float:
        jump_times = self.get_jump_times(k=k)

        # find applicable tiers
        jump_times.insert(0, 0)
        jump_rates = self.rates[-len(jump_times):]
        jump_tiers = self.tiers[-len(jump_times):]

        # construct amount function and calculate balance
        index = len([i for i in jump_times if i <= t]) - 1
        lower_t = jump_times[index]
        base_amt = max(jump_tiers[index], k)
        rate = jump_rates[index]
        time = t - lower_t

        bal = base_amt * ((1 + rate) ** time)

        return bal

    def get_jump_times(
        self,
        k: float,
    ) -> list:
        """
        Calculates the times at which the interest rate is expected to change for the account, assuming \
        an initial investment of k and no further investments.

        :param k: the principal, or initial investment.
        :type k: float
        :return: a list of times at which the interest rate is expected to change for the account.
        :rtype: list
        """
        # determine jump balances and rates
        jump_balances = [i for i in self.tiers if i > k]
        if len(jump_balances) == 0:
            jump_rates = []
        else:
            jump_rates = self.rates[:len(self.rates) - 1]
            jump_rates = jump_rates[-len(jump_balances):]

        # determine jump times
        jump_times = []
        pv = k
        t_base = 0
        for fv, i in zip(jump_balances, jump_rates):
            jump_increment = compound_solver(pv=pv, fv=fv, gr=Rate(i))
            jump_times.append(t_base + jump_increment)
            t_base = t_base + jump_increment
            pv = fv

        return jump_times


class TieredTime:
    """
    :class:`TieredTime` is a callable growth pattern for investment accounts in which the interest rate can vary \
    depending on how long the account stays open. For example, 1% for the first year, 2% for the next \
    year, and 3% afterward.

    To create a :class:`TieredTime`, supply a list of tiers and a corresponding list of interest rates for those \
    tiers. The tiers are the lower bounds for the intervals corresponding to the interest rate (the first value will \
    usually be 0).

    :param tiers: a list of tiers, for example [0, 1, 2].
    :type tiers: list
    :param rates: a list of interest rates, for example [.01, .02, .03].
    :type rates: list
    :return: a TieredTime object.
    :rtype: TieredTime
    """

    def __init__(
            self,
            tiers: list,
            rates: list,
    ):
        self.tiers = tiers
        rates_std = []
        for x in rates:
            if isinstance(x, Rate):
                pass
            elif isinstance(x, float):
                x = Rate(x)
            else:
                raise TypeError("Invalid type passed to rates, \
                use either a list of floats or Rate objects.")

            rates_std.append(x)

        self.rates = rates_std

    def __call__(
            self,
            k: float,
            t: float
    ) -> float:
        # find the cumulative tiers that apply at time t
        jump_times = self.tiers
        jump_times = [i for i in jump_times if i < t]

        rates = self.rates[:len(jump_times)]
        times = jump_times[:len(jump_times)]
        times.append(t)
        times = np.diff(times)

        # for each tier that applies, calculate the cumulative balance
        bal = k
        for rate, time in zip(rates, times):

            rate = standardize_rate(gr=rate)
            bal = bal * rate.amt_func(k=1, t=time)

        return bal


def k_solver(
    f: Callable,
    fv: float,
    t: float
) -> float:
    """
    Solver to get the initial investment K, given a growth pattern and future value.

    :param f: the growth pattern.
    :type f: Callable
    :param fv: the future value.
    :type fv: float
    :param t: the time.
    :type t: float
    :return: the initial investment, K
    :rtype: float
    """
    res = fv / f(t)

    return res


class SimpDiscAmt(Amount):
    """
    A special case of the :class:`Amount` class where discount is applied linearly. Note by discount, we mean \
    discounted interest, as in interest up front, which is not the same thing as the interest rate.

    :param k: the principal, or initial investment amount.
    :type k: float
    :param d: the discount rate.
    :type d: float
    :return: a :class:`SimpleDiscAmt` object
    :rtype: SimpDiscAmt
    """

    def __init__(
        self,
        k: float,
        d: float
    ):
        self.principal = k
        self.discount_rate = d

        Amount.__init__(
            self,
            gr=self.amt_func,
            k=k
        )

    def amt_func(self, k: float, t: float) -> float:
        """
        The amount function of the :class:`SimpDiscAmt` class.
        Automatically applied to the :class:`Amount` class
        by providing a linear discount function, instead of a user-defined one.

        :param k: the principal, or initial investment.
        :type k: float
        :param t: the time as-of time for the valuation.
        :type t: float
        :return: the value of k at time t, invested at time 0.
        :rtype: float
        """
        return k / (1 - self.discount_rate * t)


class SimpDiscAcc(Accumulation):
    """
    A special case of the :class:`Accumulation` class where discount is applied linearly. Note by discount, we mean \
    discounted interest, as in interest up front, which is not the same thing as the interest rate.

    :param d: the discount rate.
    :type d: float
    :return: a :class:`SimpDiscAcc` object
    :rtype: SimpDiscAcc
    """
    def __init__(
        self,
        d: float
    ):
        self.discount_rate = d

        Accumulation.__init__(
            self,
            gr=self.acc_func
         )

    def acc_func(self, t: float) -> float:
        """
        The accumulation function of the :class:`SimpDiscAcc` class.
        Automatically applied to the :class:`Accumulation` class
        by providing a linear discount function, instead of a user-defined one.

        :param t: the time as-of time for the valuation.
        :type t: float
        :return: the value of k at time t, invested at time 0.
        :rtype: float
        """
        return 1 / (1 - self.discount_rate * t)

    def delta_t(self, t: float) -> float:
        return self.discount_rate / (1 - self.discount_rate * t)


class SimpleLoan:
    """
    A callable growth pattern for a simple loan, which is a lump sum loan to be paid back with a single payment \
    with interest, and possibly no explicit rate given. A common type of informal loan between two people outside the \
    banking system.

    You should supply a discount amount, a discount rate, but not both.

    :param principal: the initial investment.
    :type principal: float
    :param term: the term of the loan.
    :type term: float
    :param discount_amt: the discount amount, defaults to None.
    :type discount_amt: float
    :param discount_rate: the discount_rate, defaults to None.
    :type discount_rate: float
    :return: a :class:`SimpleLoan` object when initialized, the value when called.
    :rtype: SimpleLoan when initialized, float when called.
    """

    def __init__(
        self,
        principal: float,
        term: float,
        discount_amt: float = None,
        discount_rate: float = None
    ):
        if [discount_amt, discount_rate].count(None) == 0:
            raise Exception("May supply discount amount, discount rate, but not both.")

        if [discount_amt, discount_rate].count(None) == 2:
            raise Exception("Please supply either a discount amount or rate.")

        self.principal = principal
        if discount_rate is not None:
            self.discount_rate = discount_rate
            self.discount_amt = principal * discount_rate
        else:
            self.discount_amt = discount_amt
            self.discount_rate = discount_amt / principal

        self.amount_available = principal - discount_amt
        self.term = term

    def __call__(
        self,
        k: float,
        t: float
    ) -> float:

        if not ((t == 0) or (t == self.term)):
            raise Exception("Simple loan has no meaning outside of origination or termination date.")

        if t == 0:
            return k - self.discount_amt

        if t == self.term:
            return k


class CompDiscAmt(Amount):
    """
    A special case of the :class:`Amount` class where discount is compounded. Note by discount, we mean \
    discounted interest, as in interest up front, which is not the same thing as the interest rate.

    :param k: the principal, or initial investment amount.
    :type k: float
    :param d: the discount rate.
    :type d: float
    :return: a :class:`CompDiscAmt` object
    :rtype: CompDiscAmt
    """
    def __init__(
        self,
        k: float,
        d: float
    ):
        self.principal = k
        self.discount_rate = d

        Amount.__init__(
            self,
            gr=self.amt_func,
            k=k
        )

    def amt_func(self, k, t):
        """
        The amount function of the :class:`CompDiscAmt` class.
        Automatically applied to the :class:`Amount` class
        by providing a linear compound function, instead of a user-defined one.

        :param k: the principal, or initial investment.
        :type k: float
        :param t: the time as-of time for the valuation.
        :type t: float
        :return: the value of k at time t, invested at time 0.
        :rtype: float
        """
        return k * (1 - self.discount_rate) ** (-t)


class CompDiscAcc(Accumulation):
    """
    A special case of the :class:`Accumulation` class where discount is compounded. Note by discount, we mean \
    discounted interest, as in interest up front, which is not the same thing as the interest rate.

    :param d: the discount rate.
    :type d: float
    :return: a :class:`CompDiscAcc` object
    :rtype: CompDiscAcc
    """

    def __init__(
            self,
            k: float,
            d: float
    ):
        self.principal = k
        self.discount_rate = d

        Amount.__init__(
            self,
            gr=self.acc_func,
            k=k
        )

    def acc_func(self, t):
        """
        The accumulation function of the :class:`CompDiscAcc` class.
        Automatically applied to the :class:`Accumulation` class
        by providing a compound growth function, instead of a user-defined one.
        :param t: the time as-of time for the valuation.
        :type t: float
        :return: the value of k at time t, invested at time 0.
        :rtype: float
        """
        return (1 - self.discount_rate) ** (-t)


class ForceAmt(CompoundAmt):

    def __init__(
            self,
            k: float,
            delta: float
    ):
        self.principal = k
        self.delta = delta

        CompoundAmt.__init__(
            self,
            gr=np.exp(delta) - 1,
            k=k
        )

    def amt_func(self, k, t):
        """
        The amount function of the :class:`CompoundAmt` class.
        Automatically applied to the :class:`Amount` class
        by providing a continually compounded growth function, instead of a user-defined one.

        :param k: the principal, or initial investment.
        :type k: float
        :param t: the time as-of time for the valuation.
        :type t: float
        :return: the value of k at time t, invested at time 0.
        :rtype: float
        """
        return k * np.exp(self.delta * t)


class ForceAcc(CompoundAcc):

    def __init__(
            self,
            delta: float
    ):
        self.delta = delta

        CompoundAcc.__init__(
            self,
            gr=np.exp(self.delta) - 1
        )

    def acc_func(self, t) -> float:
        """
        The accumulation function of the :class:`CompoundAcc` class.
        Automatically applied to the :class:`Accumulation` class
        by providing a compound growth function, instead of a user-defined one.

        :param t: the time as-of time for the valuation.
        :type t: float
        :return: the value of 1 unit of currency at time t, invested at time 0.
        :rtype: float
        """
        return np.exp(self.delta * t)


def simple_interval_solver(s, es):
    """
    Finds the interval at which the simple interest rate equals es

    :param s:
    :type s:
    :param es:
    :type es:
    :return:
    :rtype:
    """

    return 1 / es + 1 - 1 / s
