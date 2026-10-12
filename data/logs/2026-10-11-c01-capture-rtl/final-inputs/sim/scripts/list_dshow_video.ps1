$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;

[ComImport, Guid("29840822-5B84-11D0-BD3B-00A0C911CE86"),
 InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface ICreateDevEnum {
    [PreserveSig]
    int CreateClassEnumerator(ref Guid category, out IEnumMoniker devices, int flags);
}

[ComImport, Guid("55272A00-42CB-11CE-8135-00AA004BB851"),
 InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPropertyBag {
    [PreserveSig]
    int Read([MarshalAs(UnmanagedType.LPWStr)] string key,
        [MarshalAs(UnmanagedType.Struct)] out object value, IntPtr errorLog);
    [PreserveSig]
    int Write([MarshalAs(UnmanagedType.LPWStr)] string key,
        [MarshalAs(UnmanagedType.Struct)] ref object value);
}

public static class DirectShowVideoDevices {
    public static string[] List() {
        var category = new Guid("860BB310-5D01-11D0-BD3B-00A0C911CE86");
        var propertyBagId = new Guid("55272A00-42CB-11CE-8135-00AA004BB851");
        var devEnum = (ICreateDevEnum)Activator.CreateInstance(
            Type.GetTypeFromCLSID(new Guid("62BE5D10-60EB-11D0-BD3B-00A0C911CE86")));
        IEnumMoniker devices = null;
        var names = new System.Collections.Generic.List<string>();
        try {
            int hr = devEnum.CreateClassEnumerator(ref category, out devices, 0);
            if (hr == 1) return names.ToArray();
            Marshal.ThrowExceptionForHR(hr);
            var item = new IMoniker[1];
            while (devices.Next(1, item, IntPtr.Zero) == 0) {
                object storage = null;
                try {
                    item[0].BindToStorage(null, null, ref propertyBagId, out storage);
                    object name;
                    int readHr = ((IPropertyBag)storage).Read("FriendlyName", out name, IntPtr.Zero);
                    Marshal.ThrowExceptionForHR(readHr);
                    names.Add(Convert.ToString(name));
                } finally {
                    if (storage != null) Marshal.ReleaseComObject(storage);
                    Marshal.ReleaseComObject(item[0]);
                }
            }
        } finally {
            if (devices != null) Marshal.ReleaseComObject(devices);
            Marshal.ReleaseComObject(devEnum);
        }
        return names.ToArray();
    }
}
'@
$names = [DirectShowVideoDevices]::List()
for ($index = 0; $index -lt $names.Count; $index++) {
    "{0}`t{1}" -f $index, $names[$index]
}
if (@($names | Where-Object { $_ -eq 'USB Video' }).Count -ne 1) {
    throw 'USB Video must appear exactly once in DirectShow enumeration'
}
