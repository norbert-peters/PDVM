param(
    [Parameter(Mandatory = $true)]
    [string]$Password,

    [Parameter(Mandatory = $false)]
    [string]$PasswordFile = "C:\Users\norbe\OneDrive\Dokumente\MyApplication\scripts\secrets\pg_backup_password.txt"
)

$ErrorActionPreference = 'Stop'

$dir = Split-Path $PasswordFile -Parent
if (-not (Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

$securePassword = ConvertTo-SecureString -String $Password -AsPlainText -Force
$encrypted = ConvertFrom-SecureString -SecureString $securePassword
$encrypted | Set-Content -Path $PasswordFile -Encoding UTF8

$acl = Get-Acl $PasswordFile
$acl.SetAccessRuleProtection($true, $false)
$acl.Access | ForEach-Object { $acl.RemoveAccessRule($_) | Out-Null }
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule($currentUser, 'FullControl', 'Allow')
$acl.AddAccessRule($rule)
Set-Acl -Path $PasswordFile -AclObject $acl

Write-Host "Passwort sicher gespeichert: $PasswordFile"
