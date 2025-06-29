"""
Copyright 2023, the CVXPY Authors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import numpy as np # noqa F403
import pytest
import scipy.sparse as spar

from cvxpy.tests.base_test import BaseTest
from cvxpy.utilities import linalg as lau

try:
    import cvxpy.utilities.cpp.sparsecholesky  # noqa: F401
    missing_extension = False
except ModuleNotFoundError:
    missing_extension = True

class TestSparseCholesky(BaseTest):

    def check_gram(self, Lp, A, places=5):
        G = Lp @ Lp.T
        delta = (G - A).toarray().flatten()
        self.assertItemsAlmostEqual(delta, np.zeros(delta.size), places)

    def check_factor(self, L, places=5):
        diag = L.diagonal()
        self.assertTrue(np.all(diag > 0))
        delta = (L - spar.tril(L)).toarray().flatten()
        self.assertItemsAlmostEqual(delta, np.zeros(delta.size), places)

    @pytest.mark.skipif(missing_extension, reason="requires sparse_cholesky")
    def test_diagonal(self):
        np.random.seed(0)
        A = spar.csc_array(np.diag(np.random.rand(4)))
        _, L, p = lau.sparse_cholesky(A, 0.0)
        self.check_factor(L)
        self.check_gram(L[p, :], A)

    @pytest.mark.skipif(missing_extension, reason="requires sparse_cholesky")
    def test_tridiagonal(self):
        np.random.seed(0)
        n = 5
        diag = np.random.rand(n) + 0.1
        offdiag = np.min(np.abs(diag)) * np.ones(n - 1) / 2
        A = spar.diags_array([offdiag, diag, offdiag], offsets=[-1, 0, 1])
        _, L, p = lau.sparse_cholesky(A, 0.0)
        self.check_factor(L)
        self.check_gram(L[p, :], A)

    @pytest.mark.skipif(missing_extension, reason="requires sparse_cholesky")
    def test_generic(self, use_expression=False):
        np.random.seed(0)
        B = np.random.randn(3, 3)
        A = spar.csc_array(B @ B.T)
        if use_expression:
            from cvxpy.expressions.expression import Expression
            A = Expression.cast_to_const(A)
            assert isinstance(A, Expression)
        _, L, p = lau.sparse_cholesky(A)
        self.check_factor(L)
        if use_expression:
            A = A.value
        self.check_gram(L[p, :], A)

    @pytest.mark.skipif(missing_extension, reason="requires sparse_cholesky")
    def test_expression(self):
        self.test_generic(use_expression=True)
    
    @pytest.mark.skipif(missing_extension, reason="requires sparse_cholesky")
    def test_singular(self):
        # error on singular PSD matrix
        np.random.seed(0)
        B = np.random.randn(4, 2)
        A = B @ B.T
        with self.assertRaises(ValueError, msg=lau.SparseCholeskyMessages.EIGEN_FAIL):
            lau.sparse_cholesky(A)

    @pytest.mark.skipif(missing_extension, reason="requires sparse_cholesky")
    def test_nonsingular_indefinite(self):
        np.random.seed(0)
        n = 5
        diag = np.random.rand(n) + 0.1
        diag[n-1] = -1
        offdiag = np.min(np.abs(diag)) * np.ones(n - 1) / 2
        A = spar.diags_array([offdiag, diag, offdiag], offsets=[-1, 0, 1])
        with self.assertRaises(ValueError, msg=lau.SparseCholeskyMessages.INDEFINITE):
            lau.sparse_cholesky(A, 0.0)
