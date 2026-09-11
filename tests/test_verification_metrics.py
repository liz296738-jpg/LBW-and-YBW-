import numpy as np
import pytest
from numpy.testing import assert_allclose

from scramjet1d.verification import absolute_linf_error, relative_l1_error, relative_linf_error


def test_error_norms_use_explicit_positive_scales_without_mutating_inputs():
    numerical = np.array([1., 3.]); reference = np.array([2., 1.])
    assert absolute_linf_error(numerical, reference) == 2.
    assert relative_linf_error(numerical, reference, 4.) == .5
    assert relative_l1_error(numerical, reference, 4.) == .375
    assert_allclose(numerical, [1., 3.]); assert_allclose(reference, [2., 1.])


@pytest.mark.parametrize("numerical, reference, scale", (([1.], [np.nan], 1.), ([1.], [np.inf], 1.), ([1., 2.], [1.], 1.), ([1.], [1.], 0.)))
def test_error_norms_reject_invalid_inputs(numerical, reference, scale):
    with pytest.raises(ValueError): relative_linf_error(numerical, reference, scale)


@pytest.mark.parametrize("helper", (relative_linf_error, relative_l1_error))
@pytest.mark.parametrize("numerical, reference, scale", (([], [], 1.), ([1.], [np.nan], 1.), ([1.], [np.inf], 1.), ([1., 2.], [1.], 1.), ([1.], [1.], 0.), ([1.], [1.], -1.)))
def test_relative_metrics_directly_reject_invalid_contracts(helper, numerical, reference, scale):
    with pytest.raises(ValueError): helper(numerical, reference, scale)
