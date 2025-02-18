# Define o diretório onde os arquivos MP4 estão localizados
$diretorioMP4 = "C:\Users\metatateca\Documents\! Novas animes\CrossDebate\crossdebate mp4"

# Define o caminho completo do ffmpeg e ffprobe
$ffmpegPath = "C:\ffmpeg\bin\ffmpeg.exe"
$ffprobePath = "C:\ffmpeg\bin\ffprobe.exe"

# Verifica se os arquivos existem
if (-not (Test-Path $ffmpegPath)) {
    Write-Error "ffmpeg não encontrado em $ffmpegPath. Por favor, verifique se o arquivo existe."
    exit 1
}
if (-not (Test-Path $ffprobePath)) {
    Write-Error "ffprobe não encontrado em $ffprobePath. Por favor, verifique se o arquivo existe."
    exit 1
}

# Obtém todos os arquivos MP4 no diretório
$arquivosMP4 = Get-ChildItem -Path $diretorioMP4 -Filter "*.mp4"

# Loop através de cada arquivo MP4
foreach ($arquivo in $arquivosMP4) {
    # Obtém a duração do vídeo usando ffprobe
    $duracao = & $ffprobePath -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $arquivo.FullName
    
    # Calcula metade da duração
    $metadeDuracao = [math]::Floor([double]$duracao / 2)
    
    # Define o nome do arquivo GIF de saída
    $arquivoGIF = [System.IO.Path]::ChangeExtension($arquivo.FullName, ".gif")
    
    # Constrói os argumentos para o ffmpeg
    $argumentos = @(
        "-i"
        "$($arquivo.FullName)"
        "-vf"
        "scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
        "-t"
        "$metadeDuracao"
        "-y"
        "$arquivoGIF"
    )
    
    # Executa o ffmpeg com os argumentos definidos
    & $ffmpegPath $argumentos
    Write-Host "Arquivo '$($arquivo.Name)' convertido para GIF com duração de $metadeDuracao segundos"
}

Write-Host "Conversão concluída!"