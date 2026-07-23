Set shell = CreateObject("WScript.Shell")
Set filesystem = CreateObject("Scripting.FileSystemObject")
root = filesystem.GetParentFolderName(WScript.ScriptFullName)
shell.Run """" & filesystem.BuildPath(root, "Movaura.cmd") & """ --startup", 0, False
