function profileName = resolve_material_profile_name(defaultProfileName)
%RESOLVE_MATERIAL_PROFILE_NAME Resolve the active material profile name.

if nargin < 1 || isempty(defaultProfileName)
    defaultProfileName = 'baseline_soft_hard';
end

profileName = '';
baseVarName = 'material_profile_name';

try
    if evalin('base', sprintf('exist(''%s'', ''var'')', baseVarName))
        profileName = evalin('base', baseVarName);
    end
catch
end

if isempty(profileName)
    profileName = defaultProfileName;
end

profileName = char(string(profileName));
if isempty(strtrim(profileName))
    profileName = char(string(defaultProfileName));
end
end
