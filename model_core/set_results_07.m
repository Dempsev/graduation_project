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
    model.result.numerical('gev1').set('expr', 'solid.freq');
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
    try
        model.result.numerical('gev2').set('storetable', 'on');
    catch
    end
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
    model.result('pg2').set('xlabel', 'k');
    model.result('pg2').set('ylabel', 'Frequency (Hz)');
    model.result('pg2').set('showlegends', false);
    model.result('pg2').create('glob1', 'Global');
    model.result('pg2').feature('glob1').set('data', 'dset2');
    model.result('pg2').feature('glob1').set('expr', 'solid.freq');
    model.result('pg2').feature('glob1').set('unit', 'Hz');
    model.result('pg2').feature('glob1').set('xdata', 'expr');
    model.result('pg2').feature('glob1').set('xdataexpr', 'k');
catch
end

% Export table 1 to CSV
try
    % Re-evaluate to ensure table data exists before export
    try
        model.result.numerical('gev1').setResult;
    catch
    end
    % Create export folder if needed
    export_dir = fullfile(char(model.modelPath()), 'tbl1_exports');
    try
        java.io.File(export_dir).mkdirs();
    catch
    end
    try
        model.result.export.remove('tbl1csv');
    catch
    end
    model.result.export.create('tbl1csv', 'Table');
    model.result.export('tbl1csv').set('table', 'tbl1');
    nameStem = resolve_tbl1_name_stem();
    model.result.export('tbl1csv').set('filename', fullfile(export_dir, [nameStem '_tbl1.csv']));
    model.result.export('tbl1csv').run;
catch
end
end

function nameStem = resolve_tbl1_name_stem()
% Prefer shape-based naming (ep*_step*), fallback to timestamp-free default.
nameStem = 'tbl1';
try
    if evalin('base', 'exist(''shape_export_name'',''var'')')
        v = evalin('base', 'shape_export_name');
        if ischar(v) || isstring(v)
            vv = char(v);
            if ~isempty(strtrim(vv))
                nameStem = sanitize_file_stem(vv);
                return;
            end
        end
    end
catch
end
try
    if evalin('base', 'exist(''shape_file'',''var'')')
        sf = evalin('base', 'shape_file');
        if ischar(sf) || isstring(sf)
            [~, bn, ~] = fileparts(char(sf));
            m = regexp(bn, '(ep\d+_step\d+)', 'tokens', 'once');
            if ~isempty(m)
                nameStem = sanitize_file_stem(m{1});
                return;
            end
            nameStem = sanitize_file_stem(bn);
        end
    end
catch
end
end

function s = sanitize_file_stem(s)
% Keep filename safe and deterministic.
s = regexprep(char(s), '[^a-zA-Z0-9_\-]', '_');
if isempty(s)
    s = 'tbl1';
end
end
