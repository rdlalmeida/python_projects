/**
    This transaction triggers a cleanup routing to the VoteBox in the account that signs it. The idea is to get rid of any Ballots still present in this VoteBox that have an active Election linked to it. Elections and VoteBoxes are independent resources, but they are somewhat connected by the Ballots these hold at some point. Unfortunately, there is no direct and clean way to "inform" a VoteBox that a given Election is not online anymore (was destroyed, finished, or some other reason that prevents it from receiving more Ballots), which can lead to "zombie" Ballots in VoteBoxes, which are Ballots that were minted and deposited when the Election was still active, but the Election became unavailable before the user could submit it. The only way to get rid of this/these ballots is to delete them directly.

    The transaction retrieves a list of currently active elections from the ElectionIndex resource from the VoteBooth contract and then validates that each Ballot currently stored in the transaction's signer VoteBox. Any Ballot stored under a deactivated electionId gets destroyed.
**/
import VoteBoxStandard from 0x287f5c8b0865c516
import VoteBooth from 0x287f5c8b0865c516

transaction() {
    let voteboxOwner: Address
    let voteboxRef: auth(VoteBoxStandard.VoteBoxAdmin, Storage) &VoteBoxStandard.VoteBox
    let electionIndexPublicRef: &{VoteBooth.ElectionIndexPublic}

    prepare(signer: auth(VoteBoxStandard.VoteBoxAdmin, Storage) &Account) {
        self.voteboxRef = signer.storage.borrow<auth(VoteBoxStandard.VoteBoxAdmin, Storage) &VoteBoxStandard.VoteBox>(from: VoteBoxStandard.voteBoxStoragePath) ??
        panic(
            "Unable to retrieve a valid &VoteBoxStandard.VoteBox at `VoteBoxStandard.voteBoxStoragePath.toString()` from account `signer.address.toString()`"
        )

        self.voteboxOwner = signer.address

        let electionIndexAccount: &Account = getAccount(VoteBooth.deployerAddress)

        self.electionIndexPublicRef = electionIndexAccount.capabilities.borrow<&{VoteBooth.ElectionIndexPublic}>(VoteBooth.electionIndexPublicPath) ??
        panic(
            "Unable to get a valid &{VoteBooth.ElectionIndexPublic} at `VoteBooth.electionIndexPublicPath.toString()` from account `VoteBooth.deployerAddress.toString()`"
        )
    }

    execute {
        let activeElectionIds: [UInt64] = self.electionIndexPublicRef.getActiveElectionIds()

        let voteboxElectionIds: [UInt64] = self.voteboxRef.getActiveElectionIds()

        var inactiveBallots: Int = 0
        for voteboxElectionId in voteboxElectionIds {
            if (!activeElectionIds.contains(voteboxElectionId)) {
                // Found an inactive Ballot. Destroy it
                let burnedBallotId: UInt64? = self.voteboxRef.deleteBallot(electionId: voteboxElectionId)

                if (burnedBallotId == nil) {
                    panic(
                        "Unable to delete Ballot with election id `voteboxElectionId.toString()` from the VoteBox in account `self.voteboxOwner.toString()`"
                    )
importVoteBoxStandardfrom0xf8d6e0586b0a20c7
importVoteBoothfrom0xf8d6e0586b0a20c7

                inactiveBallots = inactiveBallots + 1
            }
        }
    }
}