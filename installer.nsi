; example1.nsi
;
; This script is perhaps one of the simplest NSIs you can make. All of the
; optional settings are left to their default settings. The installer simply 
; prompts the user asking them where to install, and drops a copy of example1.nsi
; there. 

;--------------------------------

; The name of the installer
Name "cfiler"

; The file to write
OutFile "dist\cfiler_000.exe"

; The default installation directory
InstallDir $PROGRAMFILES\cfiler

InstallDirRegKey HKLM "Software\cfiler" "InstallDir"

; Request application privileges for Windows Vista
RequestExecutionLevel admin

;--------------------------------

; Pages

Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------

; The stuff to install
Section "cfiler (required)"

  SectionIn RO
  
  !include instfiles.nsh

  WriteUninstaller "uninstall.exe"

  ; Write the installation path into the registry
  WriteRegStr HKLM Software\cfiler "InstallDir" "$INSTDIR"

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\cfiler" "DisplayName" "cfiler"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\cfiler" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\cfiler" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\cfiler" "NoRepair" 1
  WriteUninstaller "uninstall.exe"

SectionEnd ; end the section

Section "Start Menu Shortcuts"

  CreateDirectory "$SMPROGRAMS\cfiler"

  SetOutPath $INSTDIR
  CreateShortCut "$SMPROGRAMS\cfiler\cfiler.lnk" "$INSTDIR\cfiler.exe" "" "$INSTDIR\cfiler.exe" 0
  
SectionEnd


;--------------------------------

; Uninstaller

Section "Uninstall"
  
  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\cfiler"
  DeleteRegKey HKLM SOFTWARE\cfiler

  !include uninstfiles.nsh

  Delete $INSTDIR\uninstall.exe

  ; Remove shortcuts, if any
  Delete "$SMPROGRAMS\cfiler\*.*"

  ; Remove directories used
  RMDir "$SMPROGRAMS\cfiler"
  RMDir "$INSTDIR"

SectionEnd
