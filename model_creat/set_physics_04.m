function model = set_physics_04(model)
% Solid mechanics + Floquet periodic conditions based on mother.m.

if isempty(model.component.tags)
    model.component.create('comp1', true);
end

try
    model.component('comp1').common.create('mpf1', 'ParticipationFactors');
catch
end

model.component('comp1').physics.create('solid', 'SolidMechanics', 'geom1');

model.component('comp1').physics('solid').create('pc1', 'PeriodicCondition', 1);
model.component('comp1').physics('solid').feature('pc1').selection.set([1 4]);
model.component('comp1').physics('solid').feature('pc1').set('PeriodicType', 'Floquet');
model.component('comp1').physics('solid').feature('pc1').set('kFloquet', {'kx' 'ky' '0'});
model.component('comp1').physics('solid').feature('pc1').label(['kx_' native2unicode(hex2dec({'54' '68'}), 'unicode')  native2unicode(hex2dec({'67' '1f'}), 'unicode')  native2unicode(hex2dec({'60' '27'}), 'unicode')  native2unicode(hex2dec({'67' '61'}), 'unicode')  native2unicode(hex2dec({'4e' 'f6'}), 'unicode') ]);

model.component('comp1').physics('solid').create('pc2', 'PeriodicCondition', 1);
model.component('comp1').physics('solid').feature('pc2').selection.set([2 3]);
model.component('comp1').physics('solid').feature('pc2').set('PeriodicType', 'Floquet');
model.component('comp1').physics('solid').feature('pc2').set('kFloquet', {'kx' 'ky' '0'});
model.component('comp1').physics('solid').feature('pc2').label(['ky_' native2unicode(hex2dec({'54' '68'}), 'unicode')  native2unicode(hex2dec({'67' '1f'}), 'unicode')  native2unicode(hex2dec({'60' '27'}), 'unicode')  native2unicode(hex2dec({'67' '61'}), 'unicode')  native2unicode(hex2dec({'4e' 'f6'}), 'unicode') ]);
end
