import sncosmo as snc
import numpy as np
import astropy.units as u
from numpy import power as pw
from astropy.table import Table
from astropy import constants as cst
from astropy.io import fits
import yaml
from astropy.cosmology import FlatLambdaCDM
from astropy.coordinates import SkyCoord
import matplotlib.pyplot as plt

c_light_kms = cst.c.to('km/s').value
snc_mag_offset = 10.5020699 #just an offset -> set_peakmag(mb=0,'bessellb', 'ab') -> offset=2.5*log10(get_x0) change with magsys

class sn_sim :
    def __init__(self,sim_yaml):
        '''Initialisation of the simulation class with the config file'''
        #Default values
        self.dec_cmb = 48.253
        self.ra_cmb = 266.81
        self.v_cmb = 369.82
        source = snc.SALT2Source(modeldir='./SALT2/SALT2.P18_UV2IR')
        self.model=snc.Model(source=source)

        with open(sim_yaml, "r") as ymlfile:
           self.sim_cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)

        #Simulation parameters
        self.data_cfg = self.sim_cfg['data']
        self.obs_cfg_path = self.data_cfg['obs_config_path']

        self.sn_gen = self.sim_cfg['sn_gen']
        self.n_sn = int(self.sn_gen['n_sn'])

        if 'v_cmb' in self.sn_gen:
            self.v_cmb = self.sn_gen['v_cmb']

        #Cosmology parameters
        self.cosmo_cfg = self.sim_cfg['cosmology']
        self.cosmo = FlatLambdaCDM(H0=self.cosmo_cfg['H0'], Om0=self.cosmo_cfg['Om'])

        #Salt2 parameters
        self.salt2_gen = self.sim_cfg['salt2_gen']
        self.alpha = self.salt2_gen['alpha']
        self.beta = self.salt2_gen['beta']

        #Vpec parameters
        self.vpec_gen = self.sim_cfg['vpec_gen']

        self.open_obs_header()


    def simulate(self):
        '''Simulation routine'''
        #Generate z, x0, x1, c
        self.gen_param_array()
        #Simulate for each obs
        self.sim_flux=[]
        for i in range(self.n_sn):
            obs=Table.read('obs_file.fits', hdu=i+1)
            obs.convert_bytestring_to_unicode()
            self.gen_flux(obs,self.params[i])
        return

    def gen_param_array(self):
        #Init randseed in order to reproduce SNs
        self.randseed = int(self.sn_gen['randseed'])
        randseeds = np.random.default_rng(self.randseed).integers(low=1000,high=10000,size=6)
        self.randseeds = {'z_seed': randseeds[0],
                          'x0_seed': randseeds[1],
                          'x1_seed': randseeds[2],
                          'c_seed': randseeds[3],
                          'coord_seed': randseeds[4],
                          'vpec_seed': randseeds[5]
                          }
        #Init z range
        self.z_range = self.sn_gen['z_range']

        #Init vpec_gen
        self.mean_vpec = self.vpec_gen['mean_vpec']
        self.sig_vpec = self.vpec_gen['sig_vpec']

        #Init M0
        self.M0 = self.sn_gen['M0']

        #Init x1 and c
        self.mean_x1=self.salt2_gen['mean_x1']
        self.sig_x1=self.salt2_gen['sig_x1']

        self.mean_c = self.salt2_gen['mean_c']
        self.sig_c = self.salt2_gen['sig_c']

        #Redshift generation
        self.gen_redshift_cos()
        self.gen_coord()
        self.gen_z2cmb()
        self.gen_z_pec()
        self.zobs = (1+self.zcos)*(1+self.zpec)*(1+self.z2cmb)-1.

        #SALT2 params generation
        self.gen_sn_par()
        self.gen_sn_mag()

        #self.sim_t0=np.zeros(self.n_sn)
        #Total fake for the moment....
        self.sim_t0=np.array([52000+20+30*i for i in range(self.n_sn)])
        self.params = [{'z': z,
                  't0': peak,
                  'x0': x0,
                  'x1': x1,
                  'c': c
                  } for z,peak,x0,x1,c in zip(self.zobs,self.sim_t0,self.sim_x0,self.sim_x1,self.sim_c)]


    def open_obs_header(self):
        ''' Open the fits obs file header'''
        with fits.open(self.obs_cfg_path,'readonly') as obs_fits:
            self.obs_header_main = obs_fits[0].header
            self.bands = self.obs_header_main['bands'].split()
        return

    def gen_redshift_cos(self):
        self.zcos = np.random.default_rng(self.randseeds['z_seed']).uniform(low=self.z_range[0],high=self.z_range[1],size=self.n_sn)
        return

    def gen_coord(self):
        # extract ra dec from obs config
        self.ra = []
        self.dec = []
        for i in range(self.n_sn):
            obs=Table.read('obs_file.fits', hdu=i+1)
            self.ra.append(obs.meta['RA'])
            self.dec.append(obs.meta['DEC'])

        #seeds = np.random.default_rng(self.randseeds['coord_seed']).integers(low=1000,high=10000,size=2)
        #self.randseeds['ra_seed'] = seeds[0]
        #self.randseeds['dec_seed']=seeds[1]
        #self.ra = np.random.default_rng(self.randseeds['ra_seed']).uniform(low=0,high=2*np.pi,size=self.n_sn)
        #self.dec = np.random.default_rng(self.randseeds['dec_seed']).uniform(low=-np.pi/2,high=np.pi/2,size=self.n_sn)
        return

    def gen_z2cmb(self):
        # use ra dec to simulate the effect of our motion
        coordfk5 = SkyCoord(self.ra*u.deg, self.dec*u.deg, frame='fk5') #coord in fk5 frame
        galac_coord = coordfk5.transform_to('galactic')
        self.ra_gal=galac_coord.l.rad-2*np.pi*np.sign(galac_coord.l.rad)*(abs(galac_coord.l.rad)>np.pi)
        self.dec_gal=galac_coord.b.rad

        ss = np.sin(self.dec_gal)*np.sin(self.dec_cmb*np.pi/180)
        ccc = np.cos(self.dec_gal)*np.cos(self.dec_cmb*np.pi/180)*np.cos(self.ra_gal-self.ra_cmb*np.pi/180)
        self.z2cmb = (1-self.v_cmb*(ss+ccc)/c_light_kms)-1.
        return

    def gen_z_pec(self):
        self.vpec = np.random.default_rng(self.randseeds['vpec_seed']).normal(loc=self.mean_vpec,scale=self.sig_vpec,size=self.n_sn)
        self.zpec = self.vpec/c_light_kms
        return

    def gen_sn_par(self):
        ''' Generate x1 and c for the SALT2 model'''
        self.sim_x1 = np.random.default_rng(self.randseeds['x1_seed']).normal(loc=self.mean_x1,scale=self.sig_x1,size=self.n_sn)
        self.sim_c = np.random.default_rng(self.randseeds['c_seed']).normal(loc=self.mean_c,scale=self.sig_c,size=self.n_sn)
        return

    def gen_sn_mag(self):
        ''' Generate x0/mB parameters for SALT2 '''
        self.mag_smear = 0 # To change
        self.sim_mu = 5*np.log10((1+self.zcos)*(1+self.z2cmb)*pw((1+self.zpec),2)*self.cosmo.comoving_distance(self.zcos).value)+25
        #Compute mB : { mu + M0 : the standard magnitude} + {-alpha*x1 + beta*c : scattering due to color and stretch} + {intrinsic smearing}
        self.sim_mB = self.sim_mu + self.M0 - self.alpha*self.sim_x1 + self.beta*self.sim_c + self.mag_smear
        self.sim_x0 = self.x0_to_mB(self.sim_mB,1)
        return

    def gen_flux(self,obs,params):
        ''' Generate simulated flux '''
        self.sim_flux.append(snc.realize_lcs(obs, self.model, [params],scatter=False)[0])
        return

    def plot_simlc(self,lc_id,mag=False):
        '''Plot the lc_id lightcurve
           Use mag=True to plot magnitude'''
        sim_flux = self.sim_flux[lc_id]
        z = sim_flux.meta['z']
        x0 = sim_flux.meta['x0']
        x1 = sim_flux.meta['x1']
        c = sim_flux.meta['c']
        t0 = sim_flux.meta['t0']
        mb = self.x0_to_mB(x0,0)

        sim_flux_norm, time = self.norm_flux(sim_flux,25.)

        title = f'$m_B$ = {mb:.3f} $x_1$ = {x1:.3f} $c$ = {c:.4f}'

        self.model.set(z=z, c=c, t0=t0, x0=x0, x1=x1)
        time_th = np.linspace(t0-20, t0+30,100)

        plt.figure()
        plt.title(title)
        plt.xlabel('Time to peak')
        sigma=0.1 #MUST BE CHANGE BY A TRUE ERROR
        for b in self.bands:
            band_mask = sim_flux['band']==b
            sim_flux_b = sim_flux_norm[band_mask]
            time_b = time[band_mask]

            if mag:
                plt.ylabel('Mag')
                sim_flux_b = sim_flux_b[sim_flux_b>0] #Delete < 0 pts
                time_b=time_b[sim_flux_b>0]
                plot = -2.5*np.log10(sim_flux_b)+25.
                err = 2.5/np.log(10)*1/sim_flux_b*sigma
                plot_th = self.model.bandmag(b,'ab',time_th)
                plt.gca().invert_yaxis()
            else:
                plt.ylabel('Flux')
                plot = sim_flux_b
                err = sigma
                plot_th=self.model.bandflux(b,time_th,zp=25.,zpsys='ab')
            p = plt.errorbar(time_b-t0,plot,yerr=err,label=b,fmt='o')
            plt.plot(time_th-t0,plot_th, color=p[0].get_color())
        plt.legend()
        plt.show()
        return

    def norm_flux(self,flux_table,zp):
        '''Taken on sncosmo -> set the flux to the same zero-point'''
        norm_factor = pw(10,0.4*(zp-flux_table['zp']))
        flux_norm=flux_table['flux']*norm_factor
        return flux_norm,flux_table['time']

    def x0_to_mB(self,par,inv):
        if inv == 0:
            return -2.5*np.log10(par)+snc_mag_offset
        else:
            return pw(10,-0.4*(par-snc_mag_offset))

    def fit_lcs(self):
        self.fit_results = []
        for i in range(self.n_sn):
            self.model.set(z=self.sim_flux[i].meta['z'])  # set the model's redshift.
            self.fit_results.append(snc.fit_lc(self.sim_flux[i], self.model, ['t0', 'x0', 'x1', 'c']))
        return
