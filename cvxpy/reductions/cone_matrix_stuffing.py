
from cvxpy.constraints import LeqConstraint, EqConstraint
from cvxpy.utilities import QuadCoeffExtractor
import cvxpy.settings as s
import numpy as np
import scipy.sparse as sp

class ConeMatrixStuffing(Reduction):
    """Linearly constrained least squares solver via SciPy.
    """

    def accepts(self, problem):
        return (
            prob.is_dcp() and
            prob.objective.args[0].is_affine() and
            all([arg.is_affine() for c in prob.constraints for arg in c.args]))

    def get_sym_data(self, objective, constraints, cached_data=None):
        class SymData(object):
            def __init__(self, objective, constraints):
                self.constr_map = {s.EQ: constraints}
                vars_ = objective.variables()
                for c in constraints:
                    vars_ += c.variables()
                vars_ = list(set(vars_))
                self.vars_ = vars_
                self.var_offsets, self.var_sizes, self.x_length = self.get_var_offsets(vars_)

            def get_var_offsets(self, variables):
                var_offsets = {}
                var_sizes = {}
                vert_offset = 0
                for x in variables:
                    var_sizes[x.id] = x.size
                    var_offsets[x.id] = vert_offset
                    vert_offset += x.size[0]*x.size[1]
                return (var_offsets, var_sizes, vert_offset)

        return SymData(objective, constraints)

    def apply(self, problem):
        """Returns a new problem and data for inverting the new solution.
        """
        objective = problem.objective
        constraints = problem.constraints

        sym_data = self.get_sym_data(objective, constraints)

        id_map = sym_data.var_offsets
        N = sym_data.x_length

        extractor = QuadCoeffExtractor(id_map, N)

        # Extract the coefficients
        _, C, R = extractor.get_coeffs(objective.args[0])
        c = np.asarray(C.todense()).flatten()
        r = R[0]
        x = cvxpy.Variable(N)
        for c in cons:
            for i, arg in enumerate(c.args):
                _, A, b = extractor.get_coeffs(arg)
                c.args[i] = A*x + b

        new_prob = cvx.Minimize(c.T*x + r, cons)
        return (new_prob, sym_data)


    def invert(self, solution, inverse_data):
        """Returns the solution to the original problem given the inverse_data.
        """

# primal_vars: dict of id to numpy ndarray
# dual_vars: dict of id to numpy ndarray
# opt_val:
# status
        id_map = inverse_data.var_offsets
        N = inverse_data.x_length

        x = solution.primal_vars
        lmb = solution.dual_vars[0]
        nu = solution.dual_vars[1]
        status = solution.status
        ret = {
            "primal_vars": None,
            "dual_vars": None,
            "opt_val": None,
            "status": status
        }
        if status == "Optimal":
            ret.primal_vars = x
            ret.dual_vars = (lmb, nu)
        return ret