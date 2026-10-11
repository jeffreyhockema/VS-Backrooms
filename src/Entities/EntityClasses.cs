using Vintagestory.API.Common;
using Vintagestory.GameContent;

namespace Backrooms.Entities;

/// <summary>A Deathmoth flies like a butterfly, but unlike one it can be struck.</summary>
public class EntityDeathmoth : EntityButterfly
{
    public override bool IsInteractable => true;
}

/// <summary>
/// A Death Rat: its horn tips glow, faintly, red; enough to give it away under a shelf in the dark, not enough to see
/// by. (A dropped torch lights the world the same way.)
/// </summary>
public class EntityDeathRat : EntityAgent
{
    private static readonly byte[] Horns = { 0, 7, 3 };

    public override byte[] LightHsv
    {
        get => Alive ? Horns : null;
        set { }
    }
}

/// <summary>Registers the entities' behaviour, AI tasks and Firesalt with the game, on both sides.</summary>
public class EntityClasses : ModSystem
{
    public override double ExecuteOrder() => 0.05;

    public override void Start(ICoreAPI api)
    {
        api.RegisterEntityBehaviorClass("backrooms-menace", typeof(EntityBehaviorMenace));
        api.RegisterEntity("EntityDeathmoth", typeof(EntityDeathmoth));
        api.RegisterEntity("EntityDeathRat", typeof(EntityDeathRat));
        api.RegisterEntityBehaviorClass("backrooms-faceling", typeof(EntityBehaviorFaceling));
        AiTaskRegistry.Register<AiTaskCurious>("backrooms-curious");
        AiTaskRegistry.Register<AiTaskMenace>("backrooms-menace");
        AiTaskRegistry.Register<AiTaskMoth>("backrooms-moth");
        AiTaskRegistry.Register<AiTaskClump>("backrooms-clump");
        AiTaskRegistry.Register<AiTaskTheThing>("backrooms-thething");
        api.RegisterBlockClass("BackroomsFiresalt", typeof(BlockFiresalt));
        api.RegisterBlockEntityClass("BackroomsFiresalt", typeof(BlockEntityFiresalt));
    }
}
