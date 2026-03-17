function model = set_material_03(model)
% Materials based on mother.m export.

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
model.component('comp1').material('mat3').selection.set(unique(difDom));
model.component('comp1').material('mat4').selection.set(unique(intDom));

model.component('comp1').material('mat3').label([native2unicode(hex2dec({'78' '6c'}), 'unicode')  native2unicode(hex2dec({'67' '50'}), 'unicode')  native2unicode(hex2dec({'65' '99'}), 'unicode') ]);
model.component('comp1').material('mat3').propertyGroup('def').set('density', '1050');
model.component('comp1').material('mat3').propertyGroup('def').set('youngsmodulus', '3e5');
model.component('comp1').material('mat3').propertyGroup('def').set('poissonsratio', '0.49');

model.component('comp1').material('mat4').label([native2unicode(hex2dec({'8f' '6f'}), 'unicode')  native2unicode(hex2dec({'67' '50'}), 'unicode')  native2unicode(hex2dec({'65' '99'}), 'unicode') ]);
model.component('comp1').material('mat4').propertyGroup('def').set('density', '7850');
model.component('comp1').material('mat4').propertyGroup('def').set('youngsmodulus', '2.1e10');
model.component('comp1').material('mat4').propertyGroup('def').set('poissonsratio', '0.3');
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
