"""Contains function related to SALT model."""

import sncosmo as snc
import numpy as np


def n21_x1_model(z, rand_gen=None):
    """X1 distribution redshift dependant model from  Nicolas et al. 2021.

    Parameters
    ----------
    z : numpy.array(float)
        Redshift(s) of the SN.
    rand_gen: numpy.random._generator.Generator, opt
        Random generator numpy object.

    Returns
    -------
    X1 : numpy.array(float)
        Stretch parameters of supernovae.
    """
    # Just to avoid errors
    z = np.atleast_1d(z)

    # Constants defines in the paper
    a = 0.51
    K = 0.87
    mu1 = 0.37
    mu2 = -1.22
    sig1 = 0.61
    sig2 = 0.56

    # Define Gaussian function
    def gauss(mu, sig, x):
        return np.exp(-0.5 * ((x - mu) / sig)**2) / np.sqrt(2 * np.pi * sig**2)

    # Compute the pdf for old galaxy F_old(z)
    x = np.linspace(mu2 - 10 * sig2, mu1 + 10 * sig1, 100000)
    f_old = a * gauss(mu1, sig1, x)
    f_old += (1 - a) * gauss(mu2, sig2, x)
    F_old = np.cumsum(f_old) * (x[1] - x[0])

    if rand_gen is None:
        young_or_old = np.random.random(size=len(z))
        rand_normal = np.random.normal(loc=mu1, scale=sig1, size=len(z))
        rand_old = np.random.random(size=len(z))
    else:
        young_or_old = rand_gen.random(size=len(z))
        rand_normal = rand_gen.normal(loc=mu1, scale=sig1, size=len(z))
        rand_old = rand_gen.random(size=len(z))

    # Apply the pdf eq 2 from Nicolas et al. 2021
    delta_z = 1 / (1 / (K * (1 + z)**2.8) + 1)  # Probability to be young
    is_young = young_or_old < delta_z
    X1 = rand_normal * is_young
    X1 += np.interp(rand_old, F_old, x) * ~is_young
    return X1


def cov_x0_to_mb(x0, cov):
    """Convert x0,x1,c covariance into mB,x1,c covariance.

    Parameters
    ----------
    x0 : float
        SALT x0 parameter.
    cov : numpy.array(float, size = (3,3))
        SALT x0, x1, c covariance matrix

    Returns
    -------
    numpy.array(float, size = (3,3))
        SALT mb, x1, c covariance matrix.

    """
    J = np.array([[-2.5 / np.log(10) * 1 / x0, 0, 0], [0, 1, 0], [0, 0, 1]])
    new_cov = J @ cov @ J.T
    return new_cov


def compute_salt_fit_error(fit_model, cov, band, time_th, zp, magsys='ab'):
    r"""Compute fit error on flux from sncosmo fit covariance x0,x1,c.

    Parameters
    ----------
    fit_model : sncosmo.Model
        The model used to fit the sn lightcurve.
    cov : numpy.ndarray(float, size=(3,3))
        sncosmo x0,x1,c covariance matrix from SALT fit.
    band : str
        The band in which the error is computed.
    time_th : numpy.ndarray(float)
        Time for which compute the flux error.
    zp : float
        zeropoint to scale the error.
    magsys : str
        Magnitude system to use.

    Returns
    -------
    numpy.ndarray(float)
        Flux error for each input time.

    Notes
    -----
    Compute theorical fluxerr from fit :math:`err = \sqrt{COV}`
    where :math:`COV = J^T  COV(x0,x1,c)  J` with :math:`J = (dF/dx0, dF/dx1, dF/dc)`
    the jacobian.

    .. math::

        F_{norm} = \frac{x_0}{1+z} \int_\lambda \left(M_0(\lambda_s, p) + x_1 M_1(\lambda_s, p)\right)\
        10^{-0.4cCL(\lambda_s)}T_b(\lambda) \frac{\lambda}{hc} d\lambda \times \text{NF}

    where the Norm Factor is :math:`\text{NF} = 10^{0.4(ZP_{norm} -ZP_{magsys})}`.

    We found :

    .. math::
        \frac{dF}{dx_0} = \frac{F}{x_0}

    .. math::
        \frac{dF}{dx_1} = \frac{x_0}{1+z} \int_\lambda M_1(\lambda_s, p) * 10^{-0.4cCL(\lambda_s)}\
                                 T_b(\lambda)\frac{\lambda}{hc} d\lambda \times \text{NF}

    .. math::
        \frac{dF}{dc}  =  -\frac{\ln(10)}{2.5}\frac{x_0}{1+z} \int_\lambda \left(M_0(\lambda_s, p) + x_1 M_1(\lambda_s, p)\right)\
                        CL(\lambda_s)10^{-0.4 c CL(\lambda_s)}T_b(\lambda) \frac{\lambda}{hc} d\lambda \times \text{NF}

    """
    a = 1. / (1 + fit_model.parameters[0])
    t0 = fit_model.parameters[1]
    x0 = fit_model.parameters[2]
    x1 = fit_model.parameters[3]
    c = fit_model.parameters[4]
    b = snc.get_bandpass(band)
    wave, dwave = snc.utils.integration_grid(
        b.minwave(), b.maxwave(), snc.constants.MODEL_BANDFLUX_SPACING)
    trans = b(wave)
    ms = snc.get_magsystem(magsys)
    zpms = ms.zpbandflux(b)
    normfactor = 10**(0.4 * zp) / zpms
    M1 = fit_model.source._model['M1']
    M0 = fit_model.source._model['M0']
    CL = fit_model.source._colorlaw

    p = time_th - t0

    dfdx0 = fit_model.bandflux(b, time_th, zp=zp, zpsys='ab') / x0

    fint1 = M1(a * p, a * wave) * 10.**(-0.4 * CL(a * wave) * c)
    fint2 = (M0(a * p, a * wave) + x1 * M1(a * p, a * wave)) * \
        10.**(-0.4 * CL(a * wave) * c) * CL(a * wave)
    m1int = np.sum(wave * trans * fint1, axis=1) * \
        dwave / snc.constants.HC_ERG_AA
    clint = np.sum(wave * trans * fint2, axis=1) * \
        dwave / snc.constants.HC_ERG_AA

    dfdx1 = a * x0 * m1int * normfactor
    dfdc = -0.4 * np.log(10) * a * x0 * clint * normfactor
    J = np.asarray([[d1, d2, d3] for d1, d2, d3 in zip(dfdx0, dfdx1, dfdc)])
    err_th = np.sqrt(np.einsum('ki,ki->k', J, np.einsum('ij,kj->ki', cov, J)))
    return err_th
