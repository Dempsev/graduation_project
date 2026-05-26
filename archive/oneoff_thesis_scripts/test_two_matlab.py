import matlab.engine

print(matlab.engine.find_matlab())

eng1 = matlab.engine.connect_matlab('comsol_matlab')
eng2 = matlab.engine.connect_matlab('comsol_matlab_2')

eng1.eval("disp('hello from 1')", nargout=0)
eng2.eval("disp('hello from 2')", nargout=0)

print("Both connected.")