# geometry_separation
geometry separation tool based on path attribute(alembic comes from maya)
1. download otl file and reference in your hip file.
2. Fill in the file by a node, which is your imported alembic file
3. Object name is the name you want to present on geometry node and sop nodes.
4. Main group name should be a part of your path attribute.
  - check out your path attribute, for example, a path present like this .../car/body/tire/tireShape1.
  - you can type in body as main group name, then the otl will automaticaly separate all same geometry for you and create shading nodes at the 
    same time.
