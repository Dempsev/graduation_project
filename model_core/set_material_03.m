function model = set_material_03(model)
% Materials based on mother.m export.

if isempty(model.component.tags)
    model.component.create('comp1', true);
end

model.component('comp1').material.create('mat3', 'Common');
model.component('comp1').material.create('mat4', 'Common');

model.component('comp1').material('mat3').selection.set([1]);
model.component('comp1').material('mat4').selection.set([2]);

model.component('comp1').material('mat3').label([native2unicode(hex2dec({'78' '6c'}), 'unicode')  native2unicode(hex2dec({'67' '50'}), 'unicode')  native2unicode(hex2dec({'65' '99'}), 'unicode') ]);
model.component('comp1').material('mat3').propertyGroup('def').set('density', '1050');
model.component('comp1').material('mat3').propertyGroup('def').set('youngsmodulus', '3e5');
model.component('comp1').material('mat3').propertyGroup('def').set('poissonsratio', '0.49');

model.component('comp1').material('mat4').label([native2unicode(hex2dec({'8f' '6f'}), 'unicode')  native2unicode(hex2dec({'67' '50'}), 'unicode')  native2unicode(hex2dec({'65' '99'}), 'unicode') ]);
model.component('comp1').material('mat4').propertyGroup('def').set('density', '7850');
model.component('comp1').material('mat4').propertyGroup('def').set('youngsmodulus', '2.1e10');
model.component('comp1').material('mat4').propertyGroup('def').set('poissonsratio', '0.3');
end
