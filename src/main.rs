use make87;
use serde_yaml::{Mapping, Value};
use std::fs::{File, OpenOptions};
use std::io::{Read, Write};
use std::process::{Command, Stdio};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    // 1. Read mediamtx.yml from project folder
    let config_path = "mediamtx.yml";
    let mut config_str = String::new();
    File::open(config_path)?.read_to_string(&mut config_str)?;

    // 2. Parse YAML and update paths
    let mut doc: Mapping = serde_yaml::from_str(&config_str)?;

    // Ensure "paths" exists and is a mapping
    let paths_entry = doc.entry(Value::from("paths")).or_insert_with(|| Value::Mapping(Mapping::new()));
    let paths = paths_entry.as_mapping_mut().expect("paths must be a mapping");

    // Load make87 configuration to get the YouTube stream URL
    let application_config = make87::config::load_config_from_default_env()?;

    // Get the stream_url from the configuration
    let stream_url = application_config.config
        .get("stream_url")
        .and_then(|v| v.as_str())
        .ok_or("stream_url is required in configuration")?;

    println!("Configuring MediaMTX to restream YouTube URL: {}", stream_url);

    // Create a path configuration for the YouTube stream
    let mut youtube_stream_config = Mapping::new();
    youtube_stream_config.insert(Value::from("source"), Value::from(stream_url));
    youtube_stream_config.insert(Value::from("sourceOnDemand"), Value::from(true));
    youtube_stream_config.insert(Value::from("runOnInit"), Value::from("ffmpeg -re -i $MTX_SOURCE -c copy -f rtsp rtsp://localhost:$RTSP_PORT/$MTX_PATH"));
    youtube_stream_config.insert(Value::from("runOnInitRestart"), Value::from(true));

    // Add the YouTube stream path to MediaMTX configuration
    paths.insert(Value::from("youtube"), Value::Mapping(youtube_stream_config));

    // Set appropriate write queue size for streaming
    let write_queue_size = 32768;
    doc.insert(Value::from("writeQueueSize"), Value::from(write_queue_size));

    // 3. Write updated config back to mediamtx.yml
    let new_config = serde_yaml::to_string(&doc)?;
    let mut file = OpenOptions::new().write(true).truncate(true).open(config_path)?;
    file.write_all(new_config.as_bytes())?;

    // Print the config to stdout
    println!("==== Written mediamtx config ====");
    println!("{}", new_config);
    println!("=================================");

    // 4. Start the process
    let mut child = Command::new("/mediamtx")
        .stdout(Stdio::inherit())
        .stderr(Stdio::inherit())
        .spawn()?;

    // Wait for the process to exit
    let _ = child.wait()?;

    println!("mediamtx exited, shutting down...");

    Ok(())
}
