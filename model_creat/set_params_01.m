function model = set_params_01(model)
% 只做一件事：复刻“全局定义 -> 参数1/参数2”
% 注意：这里用 model.param.set 统一设置就行，不必纠结“参数1/参数2”分组，
%       分组只是GUI显示习惯，计算上等价。

% -----------------------
% 参数 1（你的截图）
% -----------------------
model.param.set('a',  '0.05[m]');   % 单胞边长
model.param.set('N',  '41');        % 路径离散点数
model.param.set('k',  '0');         % 路径参数

% 你截图里 kx, ky 是分段函数（Γ-X-M-Γ路径那种）
model.param.set('kx', 'if(k<1,(1-k)*pi/a,if(k<2,(k-1)*pi/a,pi/a))');
model.param.set('ky', 'if(k<1,(1-k)*pi/a,if(k<2,0,(k-2)*pi/a))');

% -----------------------
% 参数 2（你的截图）
% -----------------------
model.param.set('r0',  '0.012[m]'); % 花瓣平均半径
model.param.set('n',   '8');        % 花瓣数
model.param.set('phi', '0[rad]');   % 旋转角

model.param.set('amp','0.2');       % 花瓣起伏幅度（你截图写的 amp=0.2）
model.param.set('a1', '0.18');
model.param.set('b1', '0.05');
model.param.set('a2', '0.14');
model.param.set('b2', '-0.06');
model.param.set('a3', '0.06');
model.param.set('b3', '-0.05');
model.param.set('a4', '0.04');
model.param.set('b4', '-0.02');
model.param.set('a5', '0.03');
model.param.set('b5', '0.01');

end
