function [cfg, profile] = apply_material_profile_to_config(cfg, profileName)
%APPLY_MATERIAL_PROFILE_TO_CONFIG Attach the active material profile to cfg.

if nargin < 1 || ~isstruct(cfg)
    error('apply_material_profile_to_config:InvalidConfig', 'cfg must be a struct.');
end

if nargin < 2 || isempty(profileName)
    if isfield(cfg, 'materialProfile') && strlength(string(cfg.materialProfile)) > 0
        profileName = resolve_material_profile_name(cfg.materialProfile);
    else
        profileName = resolve_material_profile_name('baseline_soft_hard');
    end
end

profile = get_material_profile(profileName);
cfg.materialProfile = profile.name;
cfg.materialCase = profile.material_case;
cfg.materialProfileDescription = profile.description;
end
