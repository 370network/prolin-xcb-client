{
  inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
      pkgs = forAllSystems (system: nixpkgs.legacyPackages.${system});
    in {
      packages = forAllSystems (system: {
        default = (pkgs.${system}.callPackage ./prolin-xcb-client.nix { source = self; });
        git = (pkgs.${system}.callPackage ./prolin-xcb-client.nix { });
      });
    };
}
