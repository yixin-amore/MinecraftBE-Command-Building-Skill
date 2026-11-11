package main

import (
	"archive/zip"
	"fmt"
	"io"
	"os"
	"path/filepath"

	bwo "github.com/TriM-Organization/bedrock-world-operator/define"
	"github.com/TriM-Organization/bedrock-world-operator/world"
	"github.com/yixin-amore/AuroraStructure/structure"
)

func main() {
	if len(os.Args) < 3 {
		fmt.Fprintln(os.Stderr, "usage: bdx2mcworld <in.bdx> <out.mcworld> [startX startY startZ]")
		os.Exit(2)
	}
	in, out := os.Args[1], os.Args[2]
	sx, sy, sz := int32(0), int32(64), int32(0)
	if len(os.Args) >= 6 {
		fmt.Sscan(os.Args[3], &sx)
		fmt.Sscan(os.Args[4], &sy)
		fmt.Sscan(os.Args[5], &sz)
	}
	f, err := os.Open(in)
	if err != nil { panic(err) }
	defer f.Close()
	bd := &structure.BDX{}
	if err := bd.FromFile(f); err != nil { panic(err) }

	tmp, err := os.MkdirTemp("", "bdx2mcworld-")
	if err != nil { panic(err) }
	defer os.RemoveAll(tmp)

	bw, err := world.Open(filepath.Join(tmp, "world"), nil)
	if err != nil { panic(err) }
	if err := bd.ToMCWorld(bw, bwo.SubChunkPos{sx / 16, sy / 16, sz / 16}, nil, nil); err != nil {
		panic(err)
	}
	ld := bw.LevelDat()
	ld.LevelName = "BDX Import"
	ld.SpawnX, ld.SpawnY, ld.SpawnZ = sx, sy+1, sz
	ld.Generator = 2
	ld.CommandsEnabled = true
	ld.CommandBlocksEnabled = true
	ld.GameType = 1
	if err := bw.CloseWorld(); err != nil { panic(err) }

	if err := zipDir(filepath.Join(tmp, "world"), out); err != nil { panic(err) }
	fmt.Println("wrote", out)
}

func zipDir(dir, out string) error {
	f, err := os.Create(out)
	if err != nil { return err }
	defer f.Close()
	zw := zip.NewWriter(f)
	defer zw.Close()
	return filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil { return err }
		if info.IsDir() { return nil }
		rel, err := filepath.Rel(dir, path)
		if err != nil { return err }
		w, err := zw.Create(filepath.ToSlash(rel))
		if err != nil { return err }
		r, err := os.Open(path)
		if err != nil { return err }
		defer r.Close()
		_, err = io.Copy(w, r)
		return err
	})
}
