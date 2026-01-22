function model = set_results_07(model)
% Result framework based on mother.m (no compute).

% Tables
try
    model.result.table.create('tbl1', 'Table');
catch
end
try
    model.result.table.create('tbl2', 'Table');
catch
end

% Datasets
try
    model.result.dataset.create('dset1', 'Solution');
    model.result.dataset('dset1').set('solution', 'sol1');
catch
end
try
    model.result.dataset.create('dset2', 'Solution');
    model.result.dataset('dset2').set('solution', 'sol2');
catch
end

% Derived values: eigenfrequency + participation factors
try
    model.result.table('tbl1').clearTableData;
    model.result.numerical.create('gev1', 'EvalGlobal');
    model.result.numerical('gev1').set('data', 'dset2');
    model.result.numerical('gev1').set('table', 'tbl1');
    model.result.numerical('gev1').set('expr', 'freq');
    model.result.numerical('gev1').set('unit', 'Hz');
    model.result.numerical('gev1').set('tablecols', 'data');
    model.result.numerical('gev1').set('looplevelinput', {'all' 'all'});
    try
        model.result.numerical('gev1').set('storetable', 'on');
    catch
    end
    model.result.numerical('gev1').setResult;
catch
end
try
    model.result.numerical.create('gev2', 'EvalGlobal');
    model.result.numerical('gev2').set('data', 'dset2');
    model.result.numerical('gev2').set('table', 'tbl2');
    model.result.numerical('gev2').set('expr', {'mpf1.pfLnormX' 'mpf1.pfLnormY' 'mpf1.pfLnormZ'});
    model.result.numerical('gev2').set('tablecols', 'outer');
    model.result.numerical('gev2').set('looplevelinput', {'all' 'all'});
    model.result.numerical('gev2').setResult;
catch
end

% Evaluation groups: eigenfrequency and participation factors
try
    model.result.evaluationGroup.create('std1EvgFrq', 'EvaluationGroup');
    model.result.evaluationGroup('std1EvgFrq').label('Eigenfrequency (Study 1)');
    model.result.evaluationGroup('std1EvgFrq').set('data', 'dset2');
    model.result.evaluationGroup('std1EvgFrq').create('gev1', 'EvalGlobal');
    model.result.evaluationGroup('std1EvgFrq').feature('gev1').set('expr', {'2*pi*freq' 'imag(freq)/abs(freq)' 'abs(freq)/imag(freq)/2'});
    model.result.evaluationGroup('std1EvgFrq').feature('gev1').set('unit', {'rad/s' '1' '1'});
catch
end
try
    model.result.evaluationGroup.create('std1mpf1', 'EvaluationGroup');
    model.result.evaluationGroup('std1mpf1').label('Participation factors (Study 1)');
    model.result.evaluationGroup('std1mpf1').set('data', 'dset2');
    model.result.evaluationGroup('std1mpf1').create('gev1', 'EvalGlobal');
    model.result.evaluationGroup('std1mpf1').feature('gev1').set('expr', {'mpf1.pfLnormX' 'mpf1.pfLnormY' 'mpf1.pfLnormZ' 'mpf1.pfRnormX' 'mpf1.pfRnormY' 'mpf1.pfRnormZ'});
catch
end

% Plot group: mode shape
try
    model.result.create('pg1', 'PlotGroup2D');
    model.result('pg1').set('data', 'dset2');
    model.result('pg1').label('Mode shape (solid)');
    model.result('pg1').create('surf1', 'Surface');
    model.result('pg1').feature('surf1').set('expr', {'solid.disp'});
    model.result('pg1').feature('surf1').create('def', 'Deform');
catch
end

% Plot group: band diagram
try
    model.result.create('pg2', 'PlotGroup1D');
    model.result('pg2').set('data', 'dset2');
    model.result('pg2').label('Band diagram');
    model.result('pg2').create('glob1', 'Global');
    model.result('pg2').feature('glob1').set('expr', 'solid.freq');
catch
end

% Export table 1 to CSV
try
    model.result.export.create('tbl1csv', 'Table');
    model.result.export('tbl1csv').set('table', 'tbl1');
    model.result.export('tbl1csv').set('filename', fullfile(char(model.modelPath()), 'tbl1.csv'));
    model.result.export('tbl1csv').run;
catch
end
end
