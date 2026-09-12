FeatureScript 2500;
import(path : "onshape/std/geometry.fs", version : "2500.0");

// Original teaching geometry, not a reconstruction of a historic object.
// Z=0 is the upper bearing datum. Leg is fixed; apron seats first, top second.
// shouldered=false: parallel open slot with a horizontal bearing floor.
// shouldered=true: an integrated apron head seats on two inclined slot shoulders.
// No fillet, FDM relief or performance claim is implied by this digital baseline.

function box(context is Context, id is Id, low is Vector, high is Vector) returns Query
{
    fCuboid(context, id, { "corner1" : low, "corner2" : high });
    return qCreatedBy(id, EntityType.BODY);
}

function yzPrism(context is Context, id is Id, points is array, width is ValueWithUnits) returns Query
{
    var sketch = newSketchOnPlane(context, id + "profile", {
        "sketchPlane" : plane(vector(-width / 2, 0 * millimeter, 0 * millimeter), vector(1, 0, 0), vector(0, 1, 0))
    });
    skPolyline(sketch, "outline", { "points" : append(points, points[0]) });
    skSolve(sketch);
    opExtrude(context, id + "solid", {
        "entities" : qSketchRegion(id + "profile"), "direction" : vector(1, 0, 0),
        "endBound" : BoundingType.BLIND, "endDepth" : width
    });
    opDeleteBodies(context, id + "removeSketch", { "entities" : qCreatedBy(id + "profile", EntityType.BODY) });
    return qCreatedBy(id + "solid", EntityType.BODY);
}

function namePart(context is Context, part is Query, name is string, colour is Color)
{
    setProperty(context, { "entities" : part, "propertyType" : PropertyType.NAME, "value" : name });
    setProperty(context, { "entities" : part, "propertyType" : PropertyType.APPEARANCE, "value" : colour });
}

annotation { "Feature Type Name" : "Table node teaching pair", "Feature Type Description" : "Three-part clamp / inclined-shoulder comparison. Digital geometry only; unprinted." }
export const tableNode = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Inclined shoulders" }
        definition.shouldered is boolean;
        annotation { "Name" : "Leg square section" }
        isLength(definition.stock, LENGTH_BOUNDS);
        annotation { "Name" : "Leg below bearing datum" }
        isLength(definition.legLength, LENGTH_BOUNDS);
        annotation { "Name" : "Apron length" }
        isLength(definition.apronLength, LENGTH_BOUNDS);
        annotation { "Name" : "Apron thickness" }
        isLength(definition.apronThickness, LENGTH_BOUNDS);
        annotation { "Name" : "Apron height" }
        isLength(definition.apronHeight, LENGTH_BOUNDS);
        annotation { "Name" : "Top width" }
        isLength(definition.topWidth, LENGTH_BOUNDS);
        annotation { "Name" : "Top thickness" }
        isLength(definition.topThickness, LENGTH_BOUNDS);
        annotation { "Name" : "Twin top tenon width (X)" }
        isLength(definition.tenonWidth, LENGTH_BOUNDS);
        annotation { "Name" : "Twin top tenon thickness (Y)" }
        isLength(definition.tenonThickness, LENGTH_BOUNDS);
        annotation { "Name" : "Twin top tenon height" }
        isLength(definition.tenonHeight, LENGTH_BOUNDS);
        annotation { "Name" : "Total top fit clearance (experimental)" }
        isLength(definition.fit, NONNEGATIVE_LENGTH_BOUNDS);
        annotation { "Name" : "Clamp slot total clearance (experimental)" }
        isLength(definition.slotFit, NONNEGATIVE_LENGTH_BOUNDS);
        annotation { "Name" : "Non-bearing end gap" }
        isLength(definition.endGap, LENGTH_BOUNDS);
        annotation { "Name" : "Shoulder spread per side" }
        isLength(definition.spread, LENGTH_BOUNDS);
    }
    {
        const u = millimeter;
        const w = definition.stock;
        const h = definition.apronHeight;
        const t = definition.apronThickness;
        const l = definition.apronLength;
        const a = t / 2;
        const b = a + definition.spread;
        const tenonY = w / 2 - 2 * u;
        if (definition.legLength <= h + definition.endGap ||
            b >= tenonY - definition.tenonThickness / 2 ||
            definition.tenonWidth + definition.fit >= w ||
            definition.tenonThickness + definition.fit >= 4 * u ||
            definition.tenonHeight + definition.endGap >= definition.topThickness ||
            definition.topWidth < w || l <= w || t + definition.slotFit >= w)
            throw regenError("Invalid section, shoulder or mortise proportions");

        var leg = box(context, id + "leg", vector(-w/2, -w/2, -definition.legLength), vector(w/2, w/2, 0*u));
        var tenons = [];
        for (var side in [-1, 1])
        {
            const cy = side * tenonY;
            tenons = append(tenons, box(context, id + ("tenon" ~ side),
                vector(-definition.tenonWidth/2, cy-definition.tenonThickness/2, -1*u),
                vector(definition.tenonWidth/2, cy+definition.tenonThickness/2, definition.tenonHeight)));
        }
        opBoolean(context, id + "joinTenons", { "tools" : qUnion(append(tenons, leg)), "operationType" : BooleanOperationType.UNION });

        var slot;
        if (definition.shouldered)
        {
            // Inclined surfaces are STOP faces with zero nominal normal gap.
            // Bottom clearance ensures those faces seat before the floor.
            slot = yzPrism(context, id + "inclinedSlot", [
                vector(-a, -h-definition.endGap), vector(a, -h-definition.endGap),
                vector(a, -h), vector(b, 0*u), vector(b, definition.tenonHeight+1*u),
                vector(-b, definition.tenonHeight+1*u), vector(-b, 0*u), vector(-a, -h)
            ], w + 2*u);
        }
        else
            slot = box(context, id + "straightSlot", vector(-w/2-1*u, -a-definition.slotFit/2, -h),
                vector(w/2+1*u, a+definition.slotFit/2, definition.tenonHeight+1*u));
        opBoolean(context, id + "cutSlot", { "targets" : leg, "tools" : slot, "operationType" : BooleanOperationType.SUBTRACTION });

        var apron = box(context, id + "apron", vector(-l/2, -a, -h), vector(l/2, a, 0*u));
        if (definition.shouldered)
        {
            var head = yzPrism(context, id + "apronHead", [vector(-a,-h), vector(a,-h), vector(b,0*u), vector(-b,0*u)], w);
            opBoolean(context, id + "joinHead", { "tools" : qUnion([apron,head]), "operationType" : BooleanOperationType.UNION });
        }

        var top = box(context, id + "top", vector(-l/2,-definition.topWidth/2,0*u), vector(l/2,definition.topWidth/2,definition.topThickness));
        for (var side in [-1, 1])
        {
            const cy = side * tenonY;
            const hw = (definition.tenonWidth+definition.fit)/2;
            const ht = (definition.tenonThickness+definition.fit)/2;
            var hole = box(context, id + ("mortise" ~ side), vector(-hw,cy-ht,-1*u), vector(hw,cy+ht,definition.tenonHeight+definition.endGap));
            opBoolean(context, id + ("cutMortise" ~ side), { "targets" : top, "tools" : hole, "operationType" : BooleanOperationType.SUBTRACTION });
        }
        namePart(context, leg, "Leg", color(0.73,0.42,0.27));
        namePart(context, apron, "Apron", color(0.84,0.65,0.40));
        namePart(context, top, "Top", color(0.73,0.76,0.71));
    }, {
        "shouldered" : false, "stock" : 24*millimeter, "legLength" : 96*millimeter,
        "apronLength" : 96*millimeter, "apronThickness" : 8*millimeter, "apronHeight" : 24*millimeter,
        "topWidth" : 40*millimeter, "topThickness" : 16*millimeter,
        "tenonWidth" : 16*millimeter, "tenonThickness" : 2*millimeter, "tenonHeight" : 8*millimeter,
        "fit" : 0.3*millimeter, "slotFit" : 0.3*millimeter, "endGap" : 0.4*millimeter, "spread" : 4*millimeter
    });
