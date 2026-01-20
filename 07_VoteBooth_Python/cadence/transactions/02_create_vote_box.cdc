/**
    Transaction to create a new VoteBox resource and save it into the standard storage path defined at the contract level.

    @param recipientAddress (Address) The address of the voter account where this VoteBox should be stored into.
**/

import VoteBoxStandard from 0x287f5c8b0865c516
import Burner from 0x9a0766d93b6608b7
import VoteBooth from 0x287f5c8b0865c516

transaction() {
    prepare(signer: auth(Storage, Capabilities) &Account) {
        let newVoteBox: @VoteBoxStandard.VoteBox <- VoteBoxStandard.createVoteBox(newVoteBoxOwner: signer.address)

        // Clean up the voter's storage slot and save the new resource into it
        let oldResource: @AnyResource? <- signer.storage.load<@AnyResource>(from: VoteBoxStandard.voteBoxStoragePath)
        
        // Burn the old VoteBox using the Burner contract to trigger the burnCallback function, if this is truly a VoteBox-type resource
        Burner.burn(<- oldResource)

        signer.storage.save(<- newVoteBox, to: VoteBoxStandard.voteBoxStoragePath)
        // Repeat the process for the capabilities
        let oldCapability: Capability? = signer.capabilities.unpublish(VoteBoxStandard.voteBoxPublicPath)
        
        let newCapability: Capability<&{VoteBoxStandard.VoteBoxPublic}> = signer.capabilities.storage.issue<&{VoteBoxStandard.VoteBoxPublic}>(VoteBoxStandard.voteBoxStoragePath)
        signer.capabilities.publish(newCapability, at: VoteBoxStandard.voteBoxPublicPath)
    }

    execute {

    }
}