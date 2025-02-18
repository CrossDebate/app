# Define o diretório onde os arquivos MP4 estão localizados
$diretorioMP4 = "C:\Users\metatateca\Documents\! Novas animes\CrossDebate\crossdebate mp4"

# Define o caminho completo do ffmpeg
$ffmpegPath = "C:\ffmpeg\bin\ffmpeg.exe"

# Verifica se o arquivo ffmpeg existe
if (-not (Test-Path $ffmpegPath)) {
    Write-Error "ffmpeg não encontrado em $ffmpegPath. Por favor, verifique se o arquivo existe."
    exit 1
}

# Obtém todos os arquivos MP4 no diretório
$arquivosMP4 = Get-ChildItem -Path $diretorioMP4 -Filter "*.mp4"

# Loop através de cada arquivo MP4
foreach ($arquivo in $arquivosMP4) {
    # Define o nome do arquivo GIF de saída
    $arquivoGIF = [System.IO.Path]::ChangeExtension($arquivo.FullName, ".gif")
    
    # Constrói os argumentos para o ffmpeg
    $argumentos = @(
        "-i"
        "$($arquivo.FullName)"
        "-vf"
        "scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
        "-t"
        "10"
        "-y"
        "$arquivoGIF"
    )
    
    # Executa o ffmpeg com os argumentos definidos
    & $ffmpegPath $argumentos
    Write-Host "Arquivo '$($arquivo.Name)' convertido para '$arquivoGIF'"
}

Write-Host "Conversão concluída!"