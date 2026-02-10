#include <IGESCAFControl_Reader.hxx>
#include <STEPCAFControl_Reader.hxx>
#include <XCAFApp_Application.hxx>
#include <TDocStd_Document.hxx>
#include <IFSelect_ReturnStatus.hxx>
#include <RWGltf_CafWriter.hxx>
#include <Message_ProgressRange.hxx>
#include <TColStd_IndexedDataMapOfStringString.hxx>
#include <XCAFDoc_DocumentTool.hxx>
#include <XCAFDoc_ShapeTool.hxx>
#include <TDF_LabelSequence.hxx>
#include <TopoDS_Shape.hxx>
#include <BRepMesh_IncrementalMesh.hxx>

#include <filesystem>
#include <iostream>
#include <string>
#include <cctype>

static std::string to_lower(std::string s) {
    for (char &c : s) {
        c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    }
    return s;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        std::cerr << "usage: occt-convert <input> <output.glb>\n";
        return 2;
    }

    std::string input = argv[1];
    std::string output = argv[2];

    std::string ext = to_lower(std::filesystem::path(input).extension().string());
    if (!ext.empty() && ext[0] == '.') {
        ext = ext.substr(1);
    }

    Handle(XCAFApp_Application) app = XCAFApp_Application::GetApplication();
    Handle(TDocStd_Document) doc;
    app->NewDocument("MDTV-XCAF", doc);

    bool transferred = false;

    if (ext == "step" || ext == "stp") {
        STEPCAFControl_Reader reader;
        reader.SetColorMode(true);
        reader.SetNameMode(true);
        reader.SetLayerMode(true);
        IFSelect_ReturnStatus status = reader.ReadFile(input.c_str());
        if (status != IFSelect_RetDone) {
            std::cerr << "STEP read failed\n";
            return 3;
        }
        transferred = reader.Transfer(doc);
    } else if (ext == "iges" || ext == "igs") {
        IGESCAFControl_Reader reader;
        reader.SetColorMode(true);
        reader.SetNameMode(true);
        reader.SetLayerMode(true);
        IFSelect_ReturnStatus status = reader.ReadFile(input.c_str());
        if (status != IFSelect_RetDone) {
            std::cerr << "IGES read failed\n";
            return 4;
        }
        transferred = reader.Transfer(doc);
    } else {
        std::cerr << "unsupported extension: " << ext << "\n";
        return 5;
    }

    if (!transferred) {
        std::cerr << "transfer failed\n";
        return 6;
    }

    // Ensure triangulation exists before GLB export
    Handle(XCAFDoc_ShapeTool) shapeTool = XCAFDoc_DocumentTool::ShapeTool(doc->Main());
    if (!shapeTool.IsNull()) {
        TDF_LabelSequence labels;
        shapeTool->GetFreeShapes(labels);
        for (Standard_Integer i = 1; i <= labels.Length(); ++i) {
            TopoDS_Shape shape = shapeTool->GetShape(labels.Value(i));
            if (shape.IsNull()) {
                continue;
            }
            BRepMesh_IncrementalMesh(shape, 0.1, false, 0.5, true);
        }
    }

    RWGltf_CafWriter writer(output.c_str(), true);
    TColStd_IndexedDataMapOfStringString info;
    if (!writer.Perform(doc, info, Message_ProgressRange())) {
        std::cerr << "gltf write failed\n";
        return 7;
    }

    return 0;
}
