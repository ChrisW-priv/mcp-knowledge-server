terraform {
  backend "gcs" {
    bucket = "tf-state-mcp-knowledge-server"
    prefix = "terraform/state"
  }
}
