import numpy as np
import pysindy as ps

from ..abstractions import AbstractAlgorithm


class SINDy(AbstractAlgorithm):
    def __init__(self, 
            embed_dim: int, 
            timesteps: int, 
            max_control_cost: float = 0, 
            differentiation_method = None, 
            **kwargs):
        """
        Args:
        :param embed_dim: The dimension of the embedding space.
        :param timesteps: The number of timesteps in training trajectories.
        :param max_control_cost: The maximum control cost allowed.
        :param differentiation_method: The method used to differentiate the data. Optimization method used to fit the SINDy model. This must be a class extending pysindy.optimizers.BaseOptimizer. The default is STLSQ.

        """
        #TODO: latent dim > 1 ??? 
        assert timesteps > 2, "timesteps must be greater than 2. "
        if differentiation_method == 'smoothed_fd':
            differentiation_method = ps.SmoothedFiniteDifference(
                smoother_kws={
                    'window_length': np.log2(timesteps).astype(int), 
                    'polyorder': np.log10(timesteps).astype(int)
            })


        super().__init__(embed_dim, timesteps, max_control_cost, **kwargs)
        np.random.seed(self._seed)
        optimizer = ps.STLSQ(threshold=0.1)

        # optimizer = TrappingSR3(threshold=0.1) #TODO: add trappingSR3 for better stability
        poly_order = max(2, int(np.log2(embed_dim)//1))
        self._model = ps.SINDy(
            differentiation_method=differentiation_method,
            optimizer=optimizer,
            feature_library=ps.PolynomialLibrary(degree=poly_order)
        )

    # TODO: add control!

    def _fit(self, x: np.ndarray, **kwargs) -> None:
        # for example in x:
        #     self._model.fit(example, t=np.linspace(0, 1, self._timesteps), quiet=True)
        X = [*x]
        t = [np.linspace(0, 1, self._timesteps) for _ in range(len(x))]
        self._model.fit(X, t=t, multiple_trajectories=True, quiet=True, ensemble=True, n_models=5)

    def _predict(self, x0: np.ndarray, timesteps: int, **kwargs) -> np.ndarray:
        results = [self._model.simulate(point, np.linspace(0, 1, timesteps), integrator="odeint") for point in x0]
        results = np.array(results)
        return results
