# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# +
import matplotlib.pyplot as plt
import numpy as np
from numpy.random import normal
from commpy.utilities  import signal_power, upsample
from commpy.modulation import QAMModem
from utils.dsp import firFilter, pulseShape, lowPassFIR, edc, fourthPowerFOE, dbp, cpr
from utils.models import mzm, linFiberCh, iqm, ssfm, edfa, phaseNoise, coherentReceiver
from utils.tx import simpleWDMTx

from scipy import signal
import scipy.constants as const

# +
from IPython.core.display import HTML
from IPython.core.pylabtools import figsize
from IPython.display import display, Math

HTML("""
<style>
.output_png {
    display: table-cell;
    text-align: center;
    vertical-align: middle;
}
</style>
""")
# -

# %matplotlib inline
#figsize(7, 2.5)
figsize(10, 3)


# # Simulation of coherent WDM systems

# + [markdown] toc=true
# <h1>Table of Contents<span class="tocSkip"></span></h1>
# <div class="toc"><ul class="toc-item"><li><span><a href="#Coherent-WDM-system" data-toc-modified-id="Coherent-WDM-system-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Coherent WDM system</a></span><ul class="toc-item"><li><span><a href="#Transmitter" data-toc-modified-id="Transmitter-1.1"><span class="toc-item-num">1.1&nbsp;&nbsp;</span>Transmitter</a></span></li></ul></li></ul></div>
# -

# ## Coherent WDM system
#
# ### Transmitter

# +
# def simpleWDMTx(param):
#     """
#     Simple WDM transmitter
    
#     Generates a complex baseband waveform representing a WDM signal with arbitrary number of carriers
    
#     :param.M: QAM order [default: 16]
#     :param.Rs: carrier baud rate [baud][default: 32e9]
#     :param.SpS: samples per symbol [default: 16]
#     :param.Nbits: total number of bits per carrier [default: 60000]
#     :param.pulse: pulse shape ['nrz', 'rrc'][default: 'rrc']
#     :param.Ntaps: number of coefficients of the rrc filter [default: 4096]
#     :param.alphaRRC: rolloff do rrc filter [default: 0.01]
#     :param.Pch_dBm: launched power per WDM channel [dBm][default:-3 dBm]
#     :param.Nch: number of WDM channels [default: 5]
#     :param.Fc: central frequency of the WDM spectrum [Hz][default: 193.1e12 Hz]
#     :param.freqSpac: frequency spacing of the WDM grid [Hz][default: 40e9 Hz]
#     :param.Nmodes: number of polarization modes [default: 1]

#     """
#     # check input parameters
#     param.M     = getattr(param, 'M', 16)
#     param.Rs    = getattr(param, 'Rs', 32e9)
#     param.SpS   = getattr(param, 'SpS', 16)
#     param.Nbits = getattr(param, 'Nbits', 60000)
#     param.pulse = getattr(param, 'pulse', 'rrc')
#     param.Ntaps    = getattr(param, 'Ntaps', 4096)
#     param.alphaRRC = getattr(param, 'alphaRRC', 0.01)
#     param.Pch_dBm  = getattr(param, 'Pch_dBm', -3)
#     param.Nch      = getattr(param, 'Nch', 5)
#     param.Fc       = getattr(param, 'Fc', 193.1e12)
#     param.freqSpac = getattr(param, 'freqSpac', 50e9)
#     param.Nmodes   = getattr(param, 'Nmodes', 1)
    
#     # transmitter parameters
#     Ts  = 1/param.Rs        # symbol period [s]
#     Fa  = 1/(Ts/param.SpS)  # sampling frequency [samples/s]
#     Ta  = 1/Fa              # sampling period [s]
    
#     # central frequencies of the WDM channels
#     freqGrid = np.arange(-np.floor(param.Nch/2), np.floor(param.Nch/2)+1,1)*param.freqSpac
    
#     if (param.Nch % 2) == 0:
#         freqGrid += param.freqSpac/2
        
#     # IQM parameters
#     Ai = 1
#     Vπ = 2
#     Vb = -Vπ
#     Pch = 10**(param.Pch_dBm/10)*1e-3   # optical signal power per WDM channel
        
#     π = np.pi
#     # time array
#     t = np.arange(0, int(((param.Nbits)/np.log2(param.M))*param.SpS))
    
#     # allocate array 
#     sigTxWDM  = np.zeros((len(t), param.Nmodes), dtype='complex')
#     symbTxWDM = np.zeros((int(len(t)/param.SpS), param.Nmodes, param.Nch), dtype='complex')
    
#     Psig = 0
    
#     for indMode in range(0, param.Nmodes):        
#         print('Mode #%d'%(indMode))
        
#         for indCh in range(0, param.Nch):
#             # generate random bits
#             bitsTx   = np.random.randint(2, size=param.Nbits)    

#             # map bits to constellation symbols
#             mod = QAMModem(m=param.M)
#             symbTx = mod.modulate(bitsTx)
#             Es = mod.Es

#             # normalize symbols energy to 1
#             symbTx = symbTx/np.sqrt(Es)
            
#             symbTxWDM[:,indMode,indCh] = symbTx
            
#             # upsampling
#             symbolsUp = upsample(symbTx, param.SpS)

#             # pulse shaping
#             if param.pulse == 'nrz':
#                 pulse = pulseShape('nrz', param.SpS)
#             elif param.pulse == 'rrc':
#                 pulse = pulseShape('rrc', param.SpS, N=param.Ntaps, alpha=param.alphaRRC, Ts=Ts)

#             pulse = pulse/np.max(np.abs(pulse))
#             sigTx = firFilter(pulse, symbolsUp)

#             # optical modulation
#             sigTxCh = iqm(Ai, 0.5*sigTx, Vπ, Vb, Vb)
#             sigTxCh = np.sqrt(Pch/param.Nmodes)*sigTxCh/np.sqrt(signal_power(sigTxCh))
            
#             print('channel %d power : %.2f dBm, fc : %3.4f THz' 
#                   %(indCh+1, 10*np.log10(signal_power(sigTxCh)/1e-3), 
#                     (param.Fc+freqGrid[indCh])/1e12))

#             sigTxWDM[:,indMode] += sigTxCh*np.exp(1j*2*π*(freqGrid[indCh]/Fa)*t)
            
#         Psig += signal_power(sigTxWDM[:,indMode])
        
#     print('total WDM signal power: %.2f dBm'%(10*np.log10(Psig/1e-3)))
    
#     param.freqGrid = freqGrid
    
#     return sigTxWDM, symbTxWDM, param

# +
#def setDefaultsParams(param, func):
    
 #   if func == 'SimpleWDMTx':
        
        # default parameters
#        param.M   = getattr(param, 'M', 16)           # ordem do formato de modulação
#        Rs  = 32e9         # taxa de sinalização [baud]
#        SpS = 16           # número de amostras por símbolo
#        Nbits = 60000      # número de bits
#        pulse = 'rrc'      # formato de pulso
#        Ntaps = 4096       # número de coeficientes do filtro RRC
#        alphaRRC = 0.01    # rolloff do filtro RRC
#        Pch_dBm = -1       # potência média por canal WDM [dBm]
#        Nch     = 9        # número de canais WDM
#        Fc      = 193.1e12 # frequência central do espectro WDM
#        freqSpac = 40e9    # espaçamento em frequência da grade de canais WDM
#        Nmodes = 1         # número de modos de polarização
        
#        try:
#            param.M
#        except AttributeError:
#            otherStuff()
    
# -

class parameters:
    """
    Basic class to be used as a struct of parameters
    """
    pass


help(ssfm)

# **WDM signal generation**

# +
# Parâmetros do transmissor:
param = parameters()
#param.M   = 64           # ordem do formato de modulação
#param.Rs  = 32e9         # taxa de sinalização [baud]
#param.SpS = 16           # número de amostras por símbolo
#param.Nbits = 60000      # número de bits
#param.pulse = 'rrc'      # formato de pulso
#param.Ntaps = 4096       # número de coeficientes do filtro RRC
#param.alphaRRC = 0.01    # rolloff do filtro RRC
param.Pch_dBm = 0         # potência média por canal WDM [dBm]
#param.Nch     = 9        # número de canais WDM
#param.Fc      = 193.1e12 # frequência central do espectro WDM
#param.freqSpac = 40e9    # espaçamento em frequência da grade de canais WDM
#param.Nmodes = 1         # número de modos de polarização

sigWDM_Tx, symbTx_, param = simpleWDMTx(param)

freqGrid = param.freqGrid
# -
# **Nonlinear fiber propagation with the split-step Fourier method**

# +
linearChannel = False

# optical channel parameters
Ltotal = 800   # km
Lspan  = 80    # km
alpha = 0.2    # dB/km
D = 16         # ps/nm/km
Fc = 193.1e12  # Hz
hz = 0.5       # km
gamma = 1.3    # 1/(W.km)

if linearChannel:
    hz = Lspan  # km
    gamma = 0   # 1/(W.km)
    
sigWDM = ssfm(sigWDM_Tx, param.Rs*param.SpS, Ltotal, Lspan, hz, alpha, gamma, D, Fc, amp='edfa') 
# -

# **Optical WDM spectrum before and after transmission**

# plot psd
plt.figure()
plt.xlim(Fc-param.SpS*param.Rs/2,Fc+param.SpS*param.Rs/2);
plt.psd(sigWDM_Tx[:,0], Fs=param.SpS*param.Rs, Fc=Fc, NFFT = 4*1024, sides='twosided', label = 'WDM spectrum - Tx')
plt.psd(sigWDM, Fs=param.SpS*param.Rs, Fc=Fc, NFFT = 4*1024, sides='twosided', label = 'WDM spectrum - Rx')
plt.legend(loc='lower left')
plt.title('optical WDM spectrum');


# **WDM channels coherent detection and demodulation**

# +
### Receiver

# parameters
chIndex = 2    # index of the channel to be demodulated
plotPSD = True

Fa = param.SpS*param.Rs
Ta = 1/Fa
mod = QAMModem(m=param.M)

print('Demodulating channel #%d , fc: %.4f THz, λ: %.4f nm\n'\
      %(chIndex, (Fc + freqGrid[chIndex])/1e12, const.c/(Fc + freqGrid[chIndex])/1e-9))

sigWDM = sigWDM.reshape(len(sigWDM),)
symbTx = symbTx_[:,:,chIndex].reshape(len(symbTx_),)

# local oscillator (LO) parameters:
FO      = 64e6                 # frequency offset
Δf_lo   = freqGrid[chIndex]+FO  # downshift of the channel to be demodulated
lw      = 100e3                 # linewidth
Plo_dBm = 10                    # power in dBm
Plo     = 10**(Plo_dBm/10)*1e-3 # power in W
ϕ_lo    = 0                     # initial phase in rad    

print('Local oscillator P: %.2f dBm, lw: %.2f kHz, FO: %.2f MHz\n'\
      %(Plo_dBm, lw/1e3, FO/1e6))

# generate LO field
π       = np.pi
t       = np.arange(0, len(sigWDM))*Ta
ϕ_pn_lo = phaseNoise(lw, len(sigWDM), Ta)
sigLO   = np.sqrt(Plo)*np.exp(1j*(2*π*Δf_lo*t + ϕ_lo + ϕ_pn_lo))

# single-polarization coherent optical receiver
sigRx = coherentReceiver(sigWDM, sigLO)

# Rx filtering

# Matched filter
if param.pulse == 'nrz':
    pulse = pulseShape('nrz', param.SpS)
elif param.pulse == 'rrc':
    pulse = pulseShape('rrc', param.SpS, N=param.Ntaps, alpha=param.alphaRRC, Ts=1/param.Rs)

pulse = pulse/np.max(np.abs(pulse))            
sigRx = firFilter(pulse, sigRx)

# plot psd
if plotPSD:
    plt.figure();
   # plt.ylim(-250,-50);
    plt.psd(sigRx, Fs=Fa, NFFT = 16*1024, sides='twosided', label = 'Spectrum of the received signal')
    plt.legend(loc='upper left');
    plt.xlim(-Fa/2,Fa/2);

fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4,figsize=(15,4.5))
fig.suptitle('Sequence of DSP blocks')

ax1.plot(sigRx.real, sigRx.imag,'.', markersize=4)
ax1.axis('square')
ax1.title.set_text('Output of coherent front-end')
ax1.grid()

# digital backpropagation
# hzDBP = 5
# Pin   = 10**(param.Pch_dBm/10)*1e-3
# sigRx = sigRx/np.sqrt(signal_power(sigRx))
# sigRx = dbp(np.sqrt(Pin)*sigRx, Fa, Ltotal, Lspan, hzDBP, alpha, gamma, D, Fc)
# sigRx = sigRx.reshape(len(sigRx),)
# sigRx = firFilter(pulse, sigRx)
    
# CD compensation
sigRx = edc(sigRx, Ltotal, D, Fc-Δf_lo, Fa)

# simple timing recovery
varVector = np.var((sigRx.T).reshape(-1,param.SpS), axis=0) # finds best sampling instant
sampDelay = np.where(varVector == np.amax(varVector))[0][0]

# downsampling
sigRx = sigRx[sampDelay::param.SpS]

discard = 1000
ind = np.arange(discard, sigRx.size-discard)

# symbol normalization
sigRx = sigRx/np.sqrt(signal_power(sigRx[ind]))

# plot constellation after CD compensation
ax2.plot(sigRx.real, sigRx.imag,'.', markersize=4)
ax2.axis('square')
ax2.title.set_text('After CD comp.')
ax2.grid()

# calculate time delay due to walkoff
symbDelay = np.argmax(signal.correlate(np.abs(symbTx), np.abs(sigRx)))-sigRx.size+1 

# compensate walkoff time delay
sigRx = np.roll(sigRx, symbDelay)

# symbol normalization
sigRx = sigRx/np.sqrt(signal_power(sigRx[ind]))

# estimate and compensate LO frequency offset
fo = fourthPowerFOE(sigRx, 1/param.Rs)
print('Estimated FO : %3.4f MHz'%(fo/1e6))

sigRx = sigRx*np.exp(-1j*2*π*fo*np.arange(0,len(sigRx))/param.Rs)

# plot constellation after LO frequency offset compensation
ax3.plot(sigRx[ind].real, sigRx[ind].imag,'.', markersize=4)
ax3.axis('square')
ax3.title.set_text('After CFR (4th-power FOE)')
ax3.grid()

# compensate phase noise (carrier phase recovery - cpr)
windowSize = 40
c  = mod.constellation/np.sqrt(mod.Es)
sigRx, ϕ, θ = cpr(sigRx, windowSize, c, symbTx)

# plot phases estimated by cpr
phaseOffSet = np.mean(np.roll(ϕ_pn_lo[::param.SpS], symbDelay)-θ)
plt.figure()
plt.plot(np.roll(ϕ_pn_lo[::param.SpS], symbDelay), label='phase of the LO');
plt.plot(θ+phaseOffSet, label='phase estimated by CPR');
plt.grid()
plt.xlim(0,θ.size)
plt.legend();

# correct (possible) phase ambiguity
rot = np.mean(symbTx[ind]/sigRx[ind])
sigRx  = rot*sigRx

# symbol normalization
sigRx = sigRx/np.sqrt(signal_power(sigRx[ind]))

# plot constellation after cpr
ax4.plot(sigRx[ind].real, sigRx[ind].imag,'.', markersize=4)
ax4.axis('square')
ax4.title.set_text('After CPR (DD-PLL)')
ax4.grid()

# estimate SNR of the received constellation
SNR = signal_power(symbTx[ind])/signal_power(sigRx[ind]-symbTx[ind])

# hard decision demodulation of the received symbols    
bitsRx = mod.demodulate(np.sqrt(mod.Es)*sigRx, demod_type = 'hard') 
bitsTx = mod.demodulate(np.sqrt(mod.Es)*symbTx, demod_type = 'hard') 

err = np.logical_xor(bitsRx[discard:bitsRx.size-discard], 
                     bitsTx[discard:bitsTx.size-discard])
BER = np.mean(err)

print('Estimated SNR = %.2f dB \n'%(10*np.log10(SNR)))
print('Total counted bits = %d  '%(err.size))
print('Total of counted errors = %d  '%(err.sum()))
print('BER = %.2e  '%(BER))

plt.figure()
plt.plot(err,'o', label = 'errors location')
plt.legend()
plt.grid()

# +
plt.figure(figsize=(5,5))
plt.ylabel('$S_Q$', fontsize=14)
plt.xlabel('$S_I$', fontsize=14)
#plt.xlim(-1.1,1.1)
#plt.ylim(-1.1,1.1)
plt.grid()

plt.plot(sigRx[ind].real,sigRx[ind].imag,'.', markersize=4, label='Rx')
plt.plot(symbTx[ind].real,symbTx[ind].imag,'k.', markersize=4, label='Tx');

# +
from scipy.stats.kde import gaussian_kde

y = (sigRx[ind]).real
x = (sigRx[ind]).imag

k = gaussian_kde(np.vstack([x, y]))
k.set_bandwidth(bw_method=k.factor/4)

xi, yi = 1.1*np.mgrid[x.min():x.max():x.size**0.5*1j,y.min():y.max():y.size**0.5*1j]
zi = k(np.vstack([xi.flatten(), yi.flatten()]))
plt.figure(figsize=(5,5))
plt.pcolormesh(xi, yi, zi.reshape(xi.shape), alpha=1, shading='auto');


# -

def powerProfile(Pin, alpha, Lspan, Nspans):
    
    L = np.linspace(0, Nspans*Lspan, 2000)
    
    power = Pin-alpha*(L%Lspan)
    
    plt.plot(L, power,'')
    plt.xlabel('L [km]')
    plt.ylabel('power [dBm]')
    plt.title('Power profile')
    plt.grid()
    plt.xlim(min(L), max(L))


powerProfile(10, 0.2, 80, 10)
