'''
------------------------------------------------------------------------
Last updated: 7/18/2014
Calculates steady state of OLG model with S age cohorts, where labor
is inelastically supplied.

This py-file calls the following other file(s):
            income.py

This py-file creates the following other file(s):
    (make sure that an OUTPUT folder exists)
            OUTPUT/ss_vars.pkl
            OUTPUT/ability_3D.png
            OUTPUT/capital_dist_2D.png
            OUTPUT/capital_dist_3D.png
            OUTPUT/consumption_2D.png
            OUTPUT/consumption_3D.png
            OUTPUT/euler_errors_SS_2D.png
            OUTPUT/euler_errors_SS_3D.png
------------------------------------------------------------------------
'''

# Packages
import numpy as np
import income
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import time
import scipy.optimize as opt
import pickle

'''
------------------------------------------------------------------------
Setting up the Model
------------------------------------------------------------------------
starttime = Starting time of the program.
S         = number of periods an individual lives
J         = number of different ability groups
beta      = discount factor
sigma     = coefficient of relative risk aversion
alpha     = capital share of income
rho       = contraction parameter in steady state iteration process
            representing the weight on the new distribution gamma_new
A         = total factor productivity parameter in firms' production
            function
delta     = depreciation rate of capital
ctilde    = minimum value amount of consumption
n         = 1 x S vector of inelastic labor supply for each age s
e         = S x J matrix of age dependent possible working abilities e_s
------------------------------------------------------------------------
'''

# Parameters
starttime = time.time()
S = 60
J = 7
beta = .96 ** (60.0 / S)
sigma = 3.0
alpha = .35
rho = .20
A = 1.0
delta = 1 - (0.95 ** (60.0 / S))
ctilde = .01

if S >= 12:
    n = np.ones(S)
    n[0:S/10+1] = np.linspace(0.865, 1, (S/10)+1)
    n[- 2*((S/12)+1)+1 - ((S/6)+2): - 2*((S/12)+1)+1] = np.linspace(
        1, 0.465, (S/6)+2)
    n[- 2*((S/12)+1): -(S/12+1)+1] = np.linspace(0.465, .116, (S/12)+2)
    n[-(S/12+1):] = np.linspace(0.116, .093, (S/12)+1)
# The above method doesn't work well with very small S, so we have this
# alternative
else:
    n = np.ones(60)
    n[0:6] = np.array([.865, .8875, .91, .9325, .955, .9775])
    n[40:] = np.array(
        [.9465, .893, .8395, .786, .7325, .679, .6255, .572, .5185,
         .465, .3952, .3254, .2556, .1858, .116, .1114, .1068, .1022,
         .0976, .093])
    n = n[60 % S:: 60 / S]
e = income.get_e(S, J)

'''
------------------------------------------------------------------------
Finding the Steady State
------------------------------------------------------------------------
K_guess_init = (S-1 x J) array for the initial guess of the distribution
               of capital
solution    = (((S-1) * J) x 1) array of solution of the
               steady state distributions of capital and labor
Kssmat       = ((S-1) x J) array of the steady state distribution of
               capital
Kssvec       = ((S-1) x 1) vector of the steady state level of capital
               (averaged across ability types)
Kss          = steady state aggregate capital stock
Nss          = steady state aggregate labor
Yss          = steady state aggregate output
wss          = steady state real wage
rss          = steady state real rental rate
K_agg        = Aggregate level of capital
flag         = False if all borrowing constraints are met, true
               otherwise.
runtime      = Time needed to find the steady state (seconds)
hours        = Hours needed to find the steady state
minutes      = Minutes needed to find the steady state, less the number
               of hours
seconds      = Seconds needed to find the steady state, less the number
               of hours and minutes
------------------------------------------------------------------------
'''

# Functions and Definitions


def get_Y(K_now, N_now):
    '''
    Parameters: Aggregate capital, Aggregate labor

    Returns:    Aggregate output
    '''
    Y_now = A * (K_now ** alpha) * (N_now ** (1 - alpha))
    return Y_now


def get_w(Y_now, N_now):
    '''
    Parameters: Aggregate output, Aggregate labor

    Returns:    Returns to labor
    '''
    w_now = (1 - alpha) * Y_now / N_now
    return w_now


def get_r(Y_now, K_now):
    '''
    Parameters: Aggregate output, Aggregate capital

    Returns:    Returns to capital
    '''
    r_now = (alpha * Y_now / K_now) - delta
    return r_now


def get_N(e, n):
    '''
    Parameters: e, n

    Returns:    Aggregate labor
    '''
    N_now = np.mean(e * n.reshape(S, 1))
    return N_now


def MUc(c):
    '''
    Parameters: Consumption

    Returns:    Marginal Utility of Consumption
    '''
    output = c**(-sigma)
    return output


def MUl(l):
    '''
    Parameters: Labor

    Returns:    Marginal Utility of Labor
    '''
    output = - eta * (l ** (-xi))
    return output


def Euler_justcapital(w, r, e, n, K1, K2, K3):
    '''
    Parameters:
        w  = wage rate (scalar)
        r  = rental rate (scalar)
        e  = distribution of abilities (SxJ array)
        n  = distribution of labor (Sx1 vector)
        K1 = distribution of capital in period t ((S-1) x J array)
        K2 = distribution of capital in period t+1 ((S-1) x J array)
        K3 = distribution of capital in period t+2 ((S-1) x J array)

    Returns:
        Value of Euler error.
    '''
    euler = MUc((1 + r)*K1 + w * e[:-1, :] * n[:-1].reshape(
        S-1, 1) - K2) - beta * (1 + r)*MUc(
        (1 + r)*K2 + w * e[1:, :] * n[1:].reshape(S-1, 1) - K3)
    return euler


def Steady_State(guesses):
    '''
    Parameters: Steady state distribution of capital guess as array
                size S-1

    Returns:    Array of S-1 Euler equation errors
    '''
    K_guess = guesses
    K_guess = K_guess.reshape((S-1, J))
    K = K_guess.mean()
    N = get_N(e, n)
    Y = get_Y(K, N)
    w = get_w(Y, N)
    r = get_r(Y, K)
    K1 = np.array(list(np.zeros(J).reshape(1, J)) + list(K_guess[:-1, :]))
    K2 = K_guess
    K3 = np.array(list(K_guess[1:, :]) + list(np.zeros(J).reshape(1, J)))
    error_onlycapital = Euler_justcapital(w, r, e, n, K1, K2, K3)
    return error_onlycapital.flatten()


def borrowing_constraints(K_dist, w, r, e, n):
    '''
    Parameters:
        K_dist = Distribution of capital ((S-1)xJ array)
        w      = wage rate (scalar)
        r      = rental rate (scalar)
        e      = distribution of abilities (SxJ array)
        n      = distribution of labor (Sx1 vector)

    Returns:
        False value if all the borrowing constraints are met, True
            if there are violations.
    '''
    b_min = np.zeros((S-1, J))
    b_min[-1, :] = (ctilde - w * e[S-1, :] * n[S-1]) / (1 + r)
    for i in xrange(S-2):
        b_min[-(i+2), :] = (ctilde + b_min[-(i+1), :] - w * e[-(i+2), :] * n[-(i+2)]) / (1 + r)
    difference = K_dist - b_min
    if (difference < 0).any():
        return True
    else:
        return False

K_guess_init = np.ones((S-1, J)) / ((S-1) * J)
solution = opt.fsolve(Steady_State, K_guess_init, xtol=1e-9)

Kssmat = solution.reshape(S-1, J)
Kssvec = Kssmat.mean(1)
Kss = Kssvec.mean()
Kssvec = np.array([0]+list(Kssvec))

Nss = get_N(e, n)
Yss = get_Y(Kss, Nss)
wss = get_w(Yss, Nss)
rss = get_r(Yss, Kss)

flag = False
K_agg = Kssmat.sum()
if K_agg <= 0:
    print 'WARNING: Aggregate capital is less than or equal to zero.'
    flag = True
if borrowing_constraints(Kssmat, wss, rss, e, n) is True:
    print 'WARNING: Borrowing constraints have been violated.'
    flag = True
if flag is False:
    print 'There were no violations of the borrowing constraints.'


print "Kss:", Kss
print "Nss:", Nss
print "Yss:", Yss
print "wss:", wss
print "rss:", rss

runtime = time.time() - starttime
hours = runtime / 3600
minutes = (runtime / 60) % 60
seconds = runtime % 60
print 'Finding the steady state took %.0f hours, %.0f minutes, and %.0f \
seconds.' % (abs(hours - .5), abs(minutes - .5), seconds)


'''
------------------------------------------------------------------------
 Generate graphs of the steady-state distribution of wealth
------------------------------------------------------------------------
domain     = 1 x S vector of each age cohort
Kssmat2    = SxJ array of capital (zeros appended at the end of Kssmat2)
------------------------------------------------------------------------
'''

domain = np.linspace(1, S, S)

# 2D Graph
plt.figure(1)
plt.plot(domain, Kssvec, color='b', linewidth=2, label='Average capital stock')
plt.axhline(y=Kss, color='r', label='Steady state capital stock')
plt.title('Steady-state Distribution of Capital')
plt.legend(loc=0)
plt.xlabel(r'Age Cohorts $S$')
plt.ylabel('Capital')
plt.savefig("OUTPUT/capital_dist_2D")

# 3D Graph
cmap1 = matplotlib.cm.get_cmap('winter')
Kssmat2 = np.array(list(Kssmat) + list(np.zeros(J).reshape(1, J)))
Sgrid = np.linspace(1, S, S)
Jgrid = np.linspace(1, J, J)
X, Y = np.meshgrid(Sgrid, Jgrid)
fig2 = plt.figure(2)
ax2 = fig2.gca(projection='3d')
ax2.set_xlabel(r'age-$s$')
ax2.set_ylabel(r'ability-$j$')
ax2.set_zlabel(r'individual savings $\bar{b}_{j,s}$')
# ax2.set_title(r'Steady State Distribution of Capital Stock $K$')
ax2.plot_surface(X, Y, Kssmat2.T, rstride=1, cstride=1, cmap=cmap1)
plt.savefig('OUTPUT/capital_dist_3D')

'''
------------------------------------------------------------------------
Generate graph of Consumption
------------------------------------------------------------------------
Kssmat3 = SxJ array of capital (zeros appended at the beginning of
          Kssmat)
cssmat  = SxJ array of consumption across age and ability groups
------------------------------------------------------------------------
'''
Kssmat3 = np.array(list(np.zeros(J).reshape(1, J)) + list(Kssmat))
cssmat = (1 + rss) * Kssmat3 + wss * e * n.reshape(S, 1) - Kssmat2

# 2D Graph
plt.figure(3)
# plt.plot(domain, bsavg, label='Average capital stock')
plt.plot(domain, cssmat.mean(1), label='Consumption')
# plt.plot(domain, n * wss * e.mean(axis=1), label='Income')
plt.title('Consumption across cohorts: S = {}'.format(S))
# plt.legend(loc=0)
plt.xlabel('Age cohorts')
plt.ylabel('Consumption')
plt.savefig("OUTPUT/consumption_2D")

# 3D Graph
cmap2 = matplotlib.cm.get_cmap('jet')
fig3 = plt.figure(4)
ax3 = fig3.gca(projection='3d')
ax3.plot_surface(X, Y, cssmat.T, rstride=1, cstride=1, cmap=cmap2)
ax2.set_xlabel(r'age-$s$')
ax2.set_ylabel(r'ability-$j$')
ax3.set_zlabel('Consumption')
ax3.set_title('Steady State Distribution of Consumption')
plt.savefig('OUTPUT/consumption_3D')

'''
------------------------------------------------------------------------
Graph of Distribution of Income
------------------------------------------------------------------------
'''

# 3D Graph
cmap2 = matplotlib.cm.get_cmap('winter')
fig5 = plt.figure(5)
ax5 = fig5.gca(projection='3d')
ax5.plot_surface(X, Y, e.T, rstride=1, cstride=2, cmap=cmap2)
ax5.set_xlabel(r'age-$s$')
ax5.set_ylabel(r'ability-$j$')
ax5.set_zlabel(r'Income Level $e_j(s)$')
# ax5.set_title('Income Levels')
plt.savefig('OUTPUT/ability_3D')


'''
------------------------------------------------------------------------
Check Euler Equations
------------------------------------------------------------------------
k1          = (S-1)xJ array of Kssmat in period t-1
k2          = copy of Kssmat
k3          = (S-1)xJ array of Kssmat in period t+1
eulererrors = SxJ arry of euler errors across age and ability level
------------------------------------------------------------------------
'''

k1 = np.array(list(np.zeros(J).reshape((1, J))) + list(Kssmat[:-1, :]))
k2 = Kssmat
k3 = np.array(list(Kssmat[1:, :]) + list(np.zeros(J).reshape((1, J))))

eulererrors = Euler_justcapital(wss, rss, e, n, k1, k2, k3)

# 2D Graph
plt.figure(6)
plt.plot(domain[1:], np.abs(eulererrors).max(1))
plt.title('Euler Errors')
plt.xlabel('Age Cohorts')
plt.savefig('OUTPUT/euler_errors_SS_2D')

# 3D Graph
X2, Y2 = np.meshgrid(Sgrid[1:], Jgrid)

fig7 = plt.figure(7)
cmap2 = matplotlib.cm.get_cmap('winter')
ax7 = fig7.gca(projection='3d')
ax7.plot_surface(X2, Y2, eulererrors.T, rstride=1, cstride=2, cmap=cmap2)
ax7.set_xlabel(r'Age Cohorts $S$')
ax7.set_ylabel(r'Ability Types $J$')
ax7.set_zlabel('Error Level')
ax7.set_title('Euler Errors')
plt.savefig('OUTPUT/euler_errors_SS_3D')

'''
------------------------------------------------------------------------
Save variables/values so they can be used in other modules
------------------------------------------------------------------------
'''

var_names = ['S', 'beta', 'sigma', 'alpha', 'rho', 'A', 'delta', 'n', 'e',
             'J', 'Kss', 'Kssvec', 'Kssmat', 'Nss', 'Yss', 'wss', 'rss',
             'runtime', 'hours', 'minutes', 'seconds', 'K_agg', 'cssmat',
             'ctilde']
dictionary = {}
for key in var_names:
    dictionary[key] = globals()[key]
pickle.dump(dictionary, open("OUTPUT/ss_vars.pkl", "w"))