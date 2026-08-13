param(
  [int]$Epochs = 250
)
$log = "physx\models\ext\_deeponet_pooled.log"
$err = "physx\models\ext\_deeponet_pooled.err"
$args = @("-u", "physx/baselines.py", "--pooled-only", "--epochs", "$Epochs",
          "--threads", "2",
          "--out", "paper/fig/deeponet_baselines.json")
Start-Process -WindowStyle Hidden -FilePath 'C:\Users\sehaj\AppData\Local\Python\bin\python.exe' `
  -ArgumentList $args -WorkingDirectory 'C:\Users\sehaj\OneDrive\Desktop\age' `
  -RedirectStandardOutput $log -RedirectStandardError $err
Write-Output "launched pooled-only $Epochs epochs"
