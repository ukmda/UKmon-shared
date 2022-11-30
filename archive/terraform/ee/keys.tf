# ssh keys
resource "aws_key_pair" "marks_key" {
  key_name = "markskey"
  public_key = file("./files/ssh-keys/markskey.pub")
  tags = {
    "billingtag" = "Management"
  }
}