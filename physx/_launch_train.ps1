param(
  [string]$Law = "real",
  [int]$Seed = 0
)
$log = "physx\models\ext\lca_$Law`_s$Seed.log"
$args = @("-u", "physx/train_multi.py", "--ext", "--law", $Law, "--seed", "$Seed",
          "--epochs", "250", "--per-domain", "96",
          "--problems-json", "physx/models/ext/problems_s$Seed.json",
          "--threads", "4",
          "--save", "physx/models/ext/lca_$Law`_s$Seed.pt")
Start-Process -WindowStyle Hidden -FilePath 'C:\Users\sehaj\AppData\Local\Python\bin\python.exe' `
  -ArgumentList $args -WorkingDirectory 'C:\Users\sehaj\OneDrive\Desktop\age' `
  -RedirectStandardOutput $log -RedirectStandardError "$log.err"
Write-Output "launched $Law s$Seed"
