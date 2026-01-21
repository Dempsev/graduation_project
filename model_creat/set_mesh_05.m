function model = set_mesh_05(model)
% Mesh setup based on mother.m (default mesh1).

if isempty(model.component.tags)
    model.component.create('comp1', true);
end

if isempty(model.component('comp1').mesh.tags)
    model.component('comp1').mesh.create('mesh1');
end

model.component('comp1').mesh('mesh1').run;
end
