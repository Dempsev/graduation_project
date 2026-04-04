function text = normalize_signature_item_v1(item)
%NORMALIZE_SIGNATURE_ITEM_V1 Normalize mixed signature items into text.

if isstring(item)
    if numel(item) == 0
        text = '';
    else
        text = strjoin(cellstr(item(:)), ',');
    end
elseif iscell(item)
    if isempty(item)
        text = '';
    else
        text = strjoin(cellfun(@normalize_signature_item_v1, item, 'UniformOutput', false), ',');
    end
elseif isnumeric(item) || islogical(item)
    if isempty(item)
        text = '';
    elseif isscalar(item)
        text = char(string(item));
    else
        text = strjoin(cellstr(string(item(:))), ',');
    end
else
    text = char(string(item));
end
end
