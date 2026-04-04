function sig = file_signature_v1(pathStr)
%FILE_SIGNATURE_V1 Stable file signature helper for config signatures.

if isempty(pathStr) || ~isfile(pathStr)
    sig = 'missing';
    return;
end
info = dir(pathStr);
sig = sprintf('%s|%d|%s', pathStr, info.bytes, info.date);
end
