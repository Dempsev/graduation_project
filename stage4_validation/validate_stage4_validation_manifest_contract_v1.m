function validate_stage4_validation_manifest_contract_v1(manifestTable, manifestPath, contractJsonPath)
%VALIDATE_STAGE4_VALIDATION_MANIFEST_CONTRACT_V1 Shared preflight validation for stage4 manifests.

if nargin < 2 || isempty(manifestPath)
    manifestPath = '(in-memory manifest)';
end
if nargin < 3 || isempty(contractJsonPath)
    thisDir = fileparts(mfilename('fullpath'));
    rootDir = fileparts(thisDir);
    contractJsonPath = fullfile(rootDir, 'shared', 'contracts', 'stage4_validation_manifest_contract_v1.json');
end

if ~isfile(contractJsonPath)
    error('validate_stage4_validation_manifest_contract_v1:MissingContract', ...
        'Manifest contract JSON not found: %s', contractJsonPath);
end

payload = jsondecode(fileread(contractJsonPath));
varNames = string(manifestTable.Properties.VariableNames);

requiredColumns = string(payload.required_columns);
missing = requiredColumns(~ismember(requiredColumns, varNames));
if ~isempty(missing)
    error('validate_stage4_validation_manifest_contract_v1:MissingColumns', ...
        'Manifest %s is missing required columns: %s', manifestPath, strjoin(cellstr(missing), ', '));
end

if height(manifestTable) == 0
    error('validate_stage4_validation_manifest_contract_v1:EmptyManifest', ...
        'Manifest %s is empty.', manifestPath);
end

requiredTextColumns = string(payload.required_non_empty_columns);
for i = 1:numel(requiredTextColumns)
    name = requiredTextColumns(i);
    values = strtrim(string(manifestTable.(name)));
    lowered = lower(values);
    blanks = ismissing(values) | values == "" | lowered == "nan" | lowered == "none" | lowered == "null" | lowered == "<na>";
    if any(blanks)
        error('validate_stage4_validation_manifest_contract_v1:BlankRequiredText', ...
            'Manifest %s has blank required text values in %s at rows: %s', ...
            manifestPath, char(name), format_row_positions(blanks));
    end
end

requiredNumericColumns = string(payload.required_numeric_columns);
for i = 1:numel(requiredNumericColumns)
    name = requiredNumericColumns(i);
    values = coerce_numeric_column(manifestTable.(name));
    missingNumeric = isnan(values);
    if any(missingNumeric)
        error('validate_stage4_validation_manifest_contract_v1:InvalidRequiredNumeric', ...
            'Manifest %s has blank or non-numeric values in %s at rows: %s', ...
            manifestPath, char(name), format_row_positions(missingNumeric));
    end
end
end

function values = coerce_numeric_column(raw)
if isnumeric(raw)
    values = double(raw);
elseif islogical(raw)
    values = double(raw);
else
    values = str2double(string(raw));
end
end

function text = format_row_positions(mask)
idx = find(mask);
if isempty(idx)
    text = 'none';
    return;
end
limit = min(numel(idx), 5);
cells = arrayfun(@num2str, idx(1:limit), 'UniformOutput', false);
text = strjoin(cells, ', ');
end
