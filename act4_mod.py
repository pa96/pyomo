#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pyomo.environ import *
from pyomo.opt import SolverFactory, SolverStatus


import pandas as pd
PrintSolverOutput = False # False True

#Carga de datos
from act4_dat import *

#Crear el Modelo
model = ConcreteModel()

# for access to dual solution for constraints
model.dual = Suffix(direction=Suffix.IMPORT)

##Variables de decision
model.X = Var(T, within=NonNegativeReals)
model.S = Var(I,T, within=NonNegativeReals)
model.Y =Var(I,T, within=NonNegativeReals)
model.P =Var(T, within=NonNegativeReals)


def Objetivo(model):
    return (sum( CI[i]*model.Y[i,t] for i in I for t in T)
            + sum( CO[i]*model.S[i,t] for i in I for t in T)
            + sum( ND*model.P[t] for t in T))

model.Total_Cost= Objective(rule=Objetivo, sense = minimize)

##Restricciones


def Capmaxcomp(model,t):
    return model.X[t] <= CMAXC

def Capmaxgen(model,i,t):
    return model.Y[i,t] <= CMAXG

def Capmingen(model,i,t):
    return model.S[i,t]>=model.Y[i,t]*CMING

def Relacion(model,i,t):
    return model.S[i,t]<=model.Y[i,t]

def Balance(model,t):
    return model.P[t] == ( D[t] - model.X[t] - sum( model.S[i,t] for i in I) )


#Anexar restricciones al modelo
model.RCapmaxcomp = Constraint(T,rule=Capmaxcomp)
model.RCapmaxgen = Constraint(I,T,rule=Capmaxgen)
model.RCapmingen = Constraint(I,T,rule=Capmingen)
model.RRelacion = Constraint(I,T,rule=Relacion)
model.RBalance = Constraint(T,rule=Balance)

def pyomo_postprocess(options=None, instance=None, results=None):
    print('Función Objetivo: '+str(pyomo.environ.value(model.Total_Cost))+'\n')
    model.X.display()
    model.S.display()
    model.Y.display()
    model.P.display()
#Solver glpk
opt = SolverFactory("glpk")
resultados = opt.solve(model)

# imprimimos resultados
print("\nSolución óptima encontrada\n" + '-'*80)
pyomo_postprocess(None, None, resultados)

print( "Duals" )
from pyomo.core import Constraint
for c in model.component_objects( Constraint, active = True ):
    print( "Constraint", c )
    cobject = getattr( model, str( c ) )
    for index in cobject:
        print( "  ", index, model.dual.get(cobject[index]) )
###############################Resultado
solver = 'glpk' # ipopt glpk
if solver == 'glpk':
    opt = SolverFactory(solver)
elif solver == 'ipopt':
    solver_io = 'nl'
    opt = SolverFactory(solver,solver_io=solver_io)
if opt is None:
    print("ERROR: Unable to create solver plugin for %s using the %s interface" % (solver, solver_io))
    exit(1)

stream_solver = PrintSolverOutput # True prints solver output to screen
keepfiles = False # True prints intermediate file names (.nl,.sol,...)
results = opt.solve(model,keepfiles=keepfiles,tee=stream_solver)
model.solutions.load_from(results)

Solution = {}

if not results.solver.status == SolverStatus.ok:
    print ('results.solver.status =', results.solver.status)
else:
    Solution['ObjectiveValue'] = pyomo.environ.value(model.Total_Cost)

    Solution['Cantidad a producir en la compañía X'] = [model.X[t].value for t in T]

    Solution['Y'] = {}
    for i in I:
        Solution['Y'][i] = [model.Y[i,t].value for t in T]

    Solution['S'] = {}
    for i in I:
        Solution['S'][i] = [model.S[i,t].value for t in T]

    Solution['Cantidad de no demanda P'] = [model.P[t].value for t in T]

### Print results ###
print ('\n\nRESULTADOS')
print ('ObjectiveValue:', Solution['ObjectiveValue'])
print (pd.DataFrame(Solution['Cantidad a producir en la compañía X'], index = T, columns = ['X']))
print ('\n\nY')
print (pd.DataFrame(Solution['Y'],index = T, columns = ['GAS','SOLAR','EOLICO']))
print ('\n\nS')
print (pd.DataFrame(Solution['S'],index = T, columns = ['GAS','SOLAR','EOLICO']))
print ('\n\nP')
print (pd.DataFrame(Solution['Cantidad de no demanda P'], index = T, columns = ['P']))
print ('\n\n\n')
