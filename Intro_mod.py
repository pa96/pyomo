#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pyomo.environ import *
from pyomo.opt import SolverFactory, SolverStatus


import pandas as pd
PrintSolverOutput = False # False True

#Carga de datos
from Intro_dat import *

#Crear el Modelo
model = ConcreteModel()

# for access to dual solution for constraints
model.dual = Suffix(direction=Suffix.IMPORT)

##Variables de decision
model.X = Var(I,T, within=NonNegativeReals)
model.In = Var(I,T, within=NonNegativeReals)
model.S =Var(T, within=NonNegativeReals)


def Objetivo(model):
    return (sum(C[i]*model.X[i,t]*((1+tau[i])**(t-1))+Ch[i]*model.In[i,t]
                for i in I for t in T)
            + sum( Cs*model.S[t]
            for t in T)
            )
model.Total_Cost= Objective(rule=Objetivo, sense = minimize)

##Restricciones

def Balance(model,i,t):
    if t==1:
        return model.X[i,t] + I0[i] - model.In[i,t] == D[i,t]

    elif t>=2:
        return model.X[i,t] + model.In[i,t-1] - model.In[i,t] == D[i,t]

def Horas(model,t):
    return sum( r[i]*model.X[i,t] for i in I) <= H + model.S[t]

def Limite(model,t):
    return model.S[t] <= LS


#Anexar restricciones al modelo
model.RBalance = Constraint(I,T,rule=Balance)
model.RHoras = Constraint(T,rule=Horas)
model.RLimite = Constraint(T,rule=Limite)

def pyomo_postprocess(options=None, instance=None, results=None):
    print('Función Objetivo: '+str(pyomo.environ.value(model.Total_Cost))+'\n')
    model.X.display()
    model.In.display()
    model.S.display()

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


print ('Dual for Time: ',model.dual[model.RHoras[1]])


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
    Solution['Tiempo Extra (S)'] = [model.S[t].value for t in T]
    Solution['X'] = {}
    for i in I:
        Solution['X'][i] = [model.X[i,t].value for t in T]

    Solution['In'] = {}
    for i in I:
        Solution['In'][i] = [model.In[i,t].value for t in T]

# Export and import floating point data


### Print results ###
print ('\n\nRESULTADOS')
print ('ObjectiveValue:', Solution['ObjectiveValue'])
print ('\n\nX')
print (pd.DataFrame(Solution['X'],index = T, columns = ['A','B']))
print ('\n\nIn')
print (pd.DataFrame(Solution['In'],index = T, columns = ['A','B']))
print ('\n\nS')
print (pd.DataFrame(Solution['Tiempo Extra (S)'], columns = ['S']))
print ('\n\n\n')
