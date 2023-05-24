load("@bazel_gazelle//:deps.bzl", "gazelle_dependencies", "go_repository")

def salvo_remote_go_dependencies():
  """Loads Golang dependencies of Salvo-remote into the Bazel WORKSPACE."""
  go_repository(
    name = "com_github_hashicorp_terraform_exec",
    importpath = "github.com/hashicorp/terraform-exec",
    tag = "v0.18.1",
  )

  go_repository(
    name = "com_github_hashicorp_terraform_json",
    importpath = "github.com/hashicorp/terraform-json",
    tag = "v0.16.0",
  )

  go_repository(
    name = "com_github_hashicorp_hc_install",
    importpath = "github.com/hashicorp/hc-install",
    tag = "v0.5.2",
  )

  go_repository(
    name = "com_github_hashicorp_go_version",
    importpath = "github.com/hashicorp/go-version",
    tag = "v1.6.0",
  )

  go_repository(
    name = "com_github_hashicorp_go_cleanhttp",
    importpath = "github.com/hashicorp/go-cleanhttp",
    tag = "v0.5.2",
  )

  go_repository(
    name = "com_github_protonmail_go_crypto",
    importpath = "github.com/ProtonMail/go-crypto",
    commit = "7afd39499903116b6a11b7df39030e4f0f990bfd",
  )

  go_repository(
    name = "com_github_zclconf_go_cty",
    importpath = "github.com/zclconf/go-cty",
    tag = "v1.12.2",
  )

  go_repository(
    name = "com_github_cloudflare_circl",
    importpath = "github.com/cloudflare/circl",
    patch_args = ["-p1"],
    patches = ["//bazel:com_github_cloudflare_circl/0001-fix-cgo.patch"],
    tag = "v1.3.3",
  )

  go_repository(
    name = "com_github_google_go_cmp",
    importpath = "github.com/google/go-cmp",
    tag = "v0.5.9",
  )
