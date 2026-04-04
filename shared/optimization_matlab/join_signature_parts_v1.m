function out = join_signature_parts_v1(parts)
%JOIN_SIGNATURE_PARTS_V1 Join mixed-type signature parts into a stable string.

textParts = cell(size(parts));
for i = 1:numel(parts)
    textParts{i} = normalize_signature_item_v1(parts{i});
end

out = '';
for i = 1:numel(textParts)
    if i == 1
        out = textParts{i};
    else
        out = [out ';' textParts{i}]; %#ok<AGROW>
    end
end
end
