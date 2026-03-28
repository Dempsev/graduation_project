function model = set_material_03(model, profileSpec)
%SET_MATERIAL_03 Apply a registered material profile to the COMSOL model.

profile = resolve_material_profile_struct(profileSpec);

if isempty(model.component.tags)
    model.component.create('comp1', true);
end

try
    model.component('comp1').material('mat3');
catch
    model.component('comp1').material.create('mat3', 'Common');
end
try
    model.component('comp1').material('mat4');
catch
    model.component('comp1').material.create('mat4', 'Common');
end

intDom = get_geom_domain_ids(model, 'int1');
difDom = get_geom_domain_ids(model, 'dif1');
allDom = get_all_domain_ids(model);
if isempty(allDom)
    error('set_material_03:NoDomains', 'No geometry domains found for material assignment.');
end
if isempty(intDom) || isempty(difDom)
    error( ...
        'set_material_03:SelectionMissing', ...
        ['Failed to recover int1/dif1 domain selections for material assignment. ', ...
         'Refusing to guess, because incorrect domain mapping changes the physics.'] ...
    );
end

% Keep material tags aligned with the senior reference models:
% mat3 = soft matrix material = outer domain (difDom)
% mat4 = hard inclusion material = inner domain (intDom)
model.component('comp1').material(profile.matrix.tag).selection.set(unique(difDom));
model.component('comp1').material(profile.inclusion.tag).selection.set(unique(intDom));

apply_phase_to_material(model.component('comp1').material(profile.matrix.tag), profile.matrix);
apply_phase_to_material(model.component('comp1').material(profile.inclusion.tag), profile.inclusion);
end

function profile = resolve_material_profile_struct(profileSpec)
if nargin < 1 || isempty(profileSpec)
    profile = get_material_profile(resolve_material_profile_name('baseline_soft_hard'));
    return;
end

if ischar(profileSpec) || isstring(profileSpec)
    profile = get_material_profile(profileSpec);
    return;
end

if isstruct(profileSpec)
    if isfield(profileSpec, 'matrix') && isfield(profileSpec, 'inclusion')
        profile = profileSpec;
        return;
    end
    if isfield(profileSpec, 'materialProfile')
        profile = get_material_profile(profileSpec.materialProfile);
        return;
    end
end

error('set_material_03:InvalidProfileSpec', ...
    'profileSpec must be a profile name, a config struct with materialProfile, or a material profile struct.');
end

function apply_phase_to_material(materialObj, phase)
if strcmp(phase.role, 'soft_matrix')
    materialObj.label([native2unicode(hex2dec({'78' '6c'}), 'unicode')  native2unicode(hex2dec({'67' '50'}), 'unicode')  native2unicode(hex2dec({'65' '99'}), 'unicode') ]);
else
    materialObj.label([native2unicode(hex2dec({'8f' '6f'}), 'unicode')  native2unicode(hex2dec({'67' '50'}), 'unicode')  native2unicode(hex2dec({'65' '99'}), 'unicode') ]);
end
materialObj.propertyGroup('def').set('density', phase.density);
materialObj.propertyGroup('def').set('youngsmodulus', phase.youngsmodulus);
materialObj.propertyGroup('def').set('poissonsratio', phase.poissonsratio);
end

function ids = get_geom_domain_ids(model, featTag)
ids = [];
selTag = ['geom1_' featTag '_dom'];
try
    s = mphgetselection(model.selection(selTag));
    if isfield(s, 'entities') && ~isempty(s.entities)
        ids = unique(double(s.entities(:)'));
        return;
    end
catch
end
end

function ids = get_all_domain_ids(model)
ids = [];
try
    n = model.component('comp1').geom('geom1').getNDom;
    if n > 0
        ids = 1:n;
    end
catch
end
if isempty(ids)
    % Fallback through the difference feature selection.
    ids = get_geom_domain_ids(model, 'dif1');
end
end
