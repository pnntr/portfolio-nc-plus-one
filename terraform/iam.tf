data "aws_iam_policy_document" "instance_web_server_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "secrets_manager_policy" {
  statement {
    actions = ["secretsmanager:GetSecretValue"]

    resources = [
      "arn:aws:secretsmanager:eu-west-2:265134560735:secret:github/deploy-token-3KcJtk",
      aws_db_instance.postgres.master_user_secret[0].secret_arn
    ]
  }
}

resource "aws_iam_role" "instance" {
  name               = "instance_role"
  path               = "/system/"
  assume_role_policy = data.aws_iam_policy_document.instance_web_server_role_policy.json
}

resource "aws_iam_role_policy" "secrets_manager" {
  name   = "secrets-manager-access"
  role   = aws_iam_role.instance.id
  policy = data.aws_iam_policy_document.secrets_manager_policy.json
}

resource "aws_iam_instance_profile" "instance" {
  name = "instance_profile"
  role = aws_iam_role.instance.name
}
